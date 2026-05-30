class Cart:
    """购物车类，用来保存用户加入购物车的商品。"""

    def __init__(self, cart_id, user_id):
        # 购物车编号，用来唯一标识一个购物车
        self.cart_id = cart_id

        # 用户编号，表示这个购物车属于哪个用户
        self.user_id = user_id

        # 商品列表，用来保存购物车中的商品信息
        self.items = []
