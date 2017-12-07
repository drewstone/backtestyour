#!/usr/bin/python
# -*- coding: utf-8 -*-
from multiprocessing import Process, Queue
from multiprocessing.dummy import Process as Thread

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

import poloniex
import time

queue = Queue()

class OrderBookTickPitcher(ApplicationSession):
    """ WAMP application """
    @inlineCallbacks
    def onJoin(self, details):
        yield self.subscribe(self.onTick, 'BTC_ETH')
        yield self.subscribe(self.onTick, 'BTC_USDT')
        yield self.subscribe(self.onTick, 'ETH_USDT')
        print('Subscribed to Johnsons')

    def onTick(self, *tick):
        queue.put(tick)

    def onDisconnect(self):
        if reactor.running:
            reactor.stop()

class OrderBookTicker(object):
    """docstring for Orderbook"""
    def __init__(self):
        self.orderbook_ticker = poloniex.Poloniex().returnOrderBook()
        self._appRunner = ApplicationRunner(
            u"wss://api.poloniex.com:443", u"realm1"
        )
        self._appProcess, self._tickThread = None, None
        self._running = False

    def __call__(self, currency_pair=None):
		return self.orderbook_ticker

    def tickCatcher(self):
        print("Catching...")
        while self._running:
            try:
                tick = queue.get(timeout=1)
            except:
                continue
            else:
            	print(tick)
        print("Done catching...")

    def start(self):
        """ Start the ticker """
        print("Starting ticker")
        self._appProcess = Process(
            target=self._appRunner.run,
            args=(OrderBookTickPitcher,)
        )
        self._appProcess.daemon = True
        self._appProcess.start()
        self._running = True
        print('TICKER: orderBookTickPitcher process started')
        self._tickThread = Thread(target=self.tickCatcher)
        self._tickThread.deamon = True
        self._tickThread.start()
        print('TICKER: tickCatcher thread started')

    def stop(self):
        """ Stop the ticker """
        print("Stopping ticker")
        self._appProcess.terminate()
        print("Joining Process")
        self._appProcess.join()
        print("Joining thread")
        self._running = False
        self._tickThread.join()
        print("Ticker stopped.")

if __name__ == '__main__':
    orderbook_ticker = OrderBookTicker()
    orderbook_ticker.start()
    for i in range(10):
    	print(orderbook_ticker())
        time.sleep(1)
    orderbook_ticker.stop()
    print("Done")