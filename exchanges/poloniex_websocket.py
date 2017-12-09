import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import sys
import asyncio
import json
import threading
import time
import urllib
import urllib.request
from collections import OrderedDict

import websockets
from trading.core.ordermanager import OrderManager

GET_TICKERS_URL = 'https://poloniex.com/public?command=returnTicker'
API_LINK = 'wss://api2.poloniex.com'
SUBSCRIBE_COMMAND = '{"command":"subscribe","channel":$}'
TICKER_SUBSCRIBE = 1002
TICKER_OUTPUT = 'TICKER UPDATE {}={}(last),{}(lowestAsk),{}(highestBid),{}(percentChange),{}(baseVolume),{}(quoteVolume),{}(isFrozen),{}(high24hr),{}(low24hr)'
TRADE_OUTPUT = 'TRADE {}={}(tradeId),{}(bookSide),{}(price),{}(size),{}(timestamp)'

ORDER_LOGGING_STR = 'ooo : type = {}, price = {}, size = {}, ticker_id = {}'


poloniex_market_pairs = [
    "USDT_BTC", "USDT_ETH", "USDT_XRP", "USDT_XMR", "USDT_LTC", "USDT_ETC", "USDT_DASH", "USDT_ZEC",
    "ETH_ETC", "ETC_ZEC",
    "XMR_ZEC", "XMR_DASH", "XMR_LTC",
    "BTC_ETH", "BTC_XMR", "BTC_ETC", "BTC_LTC", "BTC_XRP", "BTC_ZEC", "BTC_DASH"
]

class PoloniexSubscriber(object):

    def __init__(self):
        tickers_data = self._get_all_tickers()
        self._tickers_list = []
        self._tickers_id = {}  # map to tranlate id (integer) to ticker name

        for ticker, data in tickers_data.items():
            if ticker in poloniex_market_pairs:
                self._tickers_id[data['id']] = ticker
                self._tickers_list.append(ticker)

        self.ob = {}
        for ticker in self._tickers_list:
            self.ob[ticker] = OrderManager()

        self._sub_thread = None
        self._event_loop = None
        self._last_seq_dic = {}

    def get_tickers(self):
        return self._tickers_list

    @staticmethod
    def _get_all_tickers():
        req = urllib.request.Request(GET_TICKERS_URL)
        with urllib.request.urlopen(req) as response:
            the_page = response.read()
        data = the_page.decode('utf8')
        data = json.loads(data)
        return data

    def start_subscribe(self):
        self._sub_thread = threading.Thread(target=self._start_subscriber)
        self._sub_thread.daemon = True
        self._sub_thread.start()

    def _start_subscriber(self):
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)
        self._event_loop.run_until_complete(self._subscribe())

    def get_prices(self):
        return list(map(lambda key: {key: self.ob[key].get_info()}, self.ob.keys()))

    async def _subscribe(self):
        async with websockets.connect(API_LINK) as websocket:
            # first subscribe to ticker channel and all tickers update channels
            await websocket.send(SUBSCRIBE_COMMAND.replace('$', str(TICKER_SUBSCRIBE)))
            for ticker in self._tickers_list:
                req = SUBSCRIBE_COMMAND.replace('$', '\"' + ticker + '\"')
                await websocket.send(req)

            # now parse received data
            while True:
                message = await websocket.recv()
                self.handle_message(message)

    def handle_orderbook_snapshot(self, asks, bids):
        for price, size in [order for order in asks]:
            order = ('limit', ticker_id, float(price), -float(size))
            self.ob[ticker_id].add_order(*order)
            print(ORDER_LOGGING_STR.format(*order))

        # BIDS
        for price, size in [order for order in bids]:
            order = ('limit', ticker_id, float(price), float(size))
            self.ob[ticker_id].add_order(*order)
            print(ORDER_LOGGING_STR.format(*order))

        sys.stdout.flush()


    def handle_orderbook_update(self, side, ticker_id, price, size):
        # this mean remove
        if size == '0.00000000':
            print('Remove {},side={},price={}'.format(
                ticker_id, side, price))
        # this mean add or change
        else:
            print('Add or change {},side={},price={},size={}'.format(
                ticker_id, side, price, size))

        # Add check if necessary to see if new order crosses spread (LIMIT OR MARKET)

        if side == 'ask':
            order = ('limit', ticker_id, price, -size)
        else:
            order = ('limit', ticker_id, price, size)

        self.ob[ticker_id].add_order(*order)

        print(ORDER_LOGGING_STR.format(*order))
        sys.stdout.flush()


    def handle_message(self, message):
        data = json.loads(message, object_pairs_hook=OrderedDict)

        if 'error' in data:
            raise Exception('error arrived message={}'.format(message))

        if data[0] == 1010:
            # this mean heartbeat
            continue
        if len(data) < 2:
            raise Exception(
                'Short message arrived message={}'.format(message))
        if data[1] == 1:
            # this mean the subscription is success
            continue
        if data[1] == 0:
            # this mean the subscription is failure
            raise Exception(
                'subscription failed message={}'.format(message))
        if data[0] == TICKER_SUBSCRIBE:
            values = data[2]
            ticker_id_int = values[0]
            # last = values[1]
            # lowestAsk = values[2]
            # highestBid = values[3]
            # percentChange = values[4]
            # baseVolume = values[5]
            # quoteVolume = values[6]
            # isFrozen = values[7]
            # high24hr = values[8]
            # low24hr = values[9]
            ticker_id = self._tickers_id[ticker_id_int]
            out_list = [ticker_id] + values[1:]
            # print(TICKER_OUTPUT.format(*out_list))
        else:
            ticker_id = self._tickers_id[data[0]]
            seq = data[1]

            for update in data[2]:
                # this mean this is snapshot
                if update[0] == 'i':
                    # UPDATE[1]['currencyPair'] is the ticker name
                    self._last_seq_dic[ticker_id] = seq

                    asks = update[1]['orderBook'][0].items()
                    bids = update[1]['orderBook'][1].items()

                    self.handle_orderbook_snapshot(asks, bids)

                # this mean add or change or remove
                elif update[0] == 'o':
                    if self._last_seq_dic[ticker_id] + 1 != seq:
                        raise Exception('Problem with seq number prev_seq={},message={}'.format(
                            self._last_seq_dic[ticker_id], message))

                    price = float(update[2])
                    side = 'bid' if update[1] == 1 else 'ask'
                    size = float(update[3])

                    self.handle_orderbook_update(side, ticker_id, price, size)

                # this mean trade
                elif update[0] == 't':
                    if self._last_seq_dic[ticker_id] + 1 != seq:
                        raise Exception('Problem with seq number prev_seq={},message={}'.format(
                            self._last_seq_dic[ticker_id], message))
                    print(update)
                    trade_id = update[1]
                    book_side = 'bid' if update[2] == 1 else 'ask'
                    price = update[3]
                    size = update[4]
                    timestamp = update[5]
                    out_list = [ticker_id, trade_id,
                                book_side, price, size, timestamp]
                    # print(TRADE_OUTPUT.format(*out_list))

            self._last_seq_dic[ticker_id] = seq


if __name__ == '__main__':
    sub = PoloniexSubscriber()
    sub.start_subscribe()
    try:
        for i in range(10):
            time.sleep(1)
    except KeyboardInterrupt:
        # quit
        pass
    print(sub.get_prices())
