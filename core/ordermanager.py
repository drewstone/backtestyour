import numpy as np
from .orderbook import OrderBook

class Order(object):
	"""A simple order class"""
	def __init__(self, type, price, quantity):
		super(Order, self).__init__()
		self.type = type
		self.price = price
		self.quantity = quantity
	
class OrderManager(object):
	"""docstring for Orderbook"""
	def __init__(self):
		super(OrderManager, self).__init__()
		self.lob = OrderBook()

	def get_quote(self, order_type, trading_id, price, quantity):
		sign = np.sign(quantity)

		quote = {
			'type': order_type,
			'trading_id': trading_id,
			'price': price,
			'qty': sign * quantity,
			'tid': self.lob.time
		}

		if sign < 0:
			quote['side'] = 'ask'
		else:
			quote['side'] = 'bid'

		return quote

	def get_info(self):
		return (self.lob.time, self.lob.getBestBid(), self.lob.getBestAsk())

	def get_lob(self):
		return self.lob

	def add_order(self, order_type, trading_id, price, quantity):
		quote = self.get_quote(order_type, trading_id, price, quantity)
		self.lob.processOrder(quote, fromData=False, verbose=False)
		return quote
