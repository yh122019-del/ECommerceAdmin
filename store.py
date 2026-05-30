class Store:
    """商城类，用来统一管理用户、商品、购物车和订单。"""

    def __init__(self):
        # 用户列表，用来保存所有用户对象
        self.users = []

        # 商品列表，用来保存所有商品对象
        self.products = []

        # 购物车列表，用来保存所有购物车对象
        self.carts = []

        # 订单列表，用来保存所有订单对象
        self.orders = []
