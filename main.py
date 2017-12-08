from core.ordermanager import OrderManager
# from ordermanager import OrderManager

if __name__ == '__main__':
	om = OrderManager()
	om.add_order('limit', 1, 0.000000000099999999999999999, -0.00000100)
	om.add_order('limit', 1, 0.0000000000999999999999999999, -0.0000300)
	om.add_order('limit', 1, 0.0000000000999999999999999999, -0.0000300)
	om.add_order('limit', 1, 0.0000000000799999999999999999, 0.0000300)
	om.add_order('limit', 1, 0.0000000000699999999999999999, 0.0000300)
	om.add_order('limit', 1, 0.0000000000699999999999999999, 0.0000300)
	om.add_order('limit', 1, 0.0000000000799999999999999999, -0.0000300)
	om.add_order('limit', 1, 0.0000000000799999999999999999, -0.0000300)
	print(om.get_info())