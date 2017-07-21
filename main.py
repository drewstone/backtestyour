from core.ordermanager import OrderManager
# from ordermanager import OrderManager

if __name__ == '__main__':
	om = OrderManager()
	om.add_order('limit', 1, 0.9, -100)
	om.add_order('limit', 1, 0.9, -100)
	om.add_order('limit', 1, 0.9, -100)
	om.add_order('limit', 1, 0.7, 100)
	om.add_order('limit', 1, 0.6, 100)
	om.add_order('limit', 1, 0.6, 100)
	om.add_order('limit', 1, 0.7, -100)
	om.add_order('limit', 1, 0.7, -100)
	print(om.get_info())