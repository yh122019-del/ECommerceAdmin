class Order:
    """订单类，用来保存用户下单后的订单信息。"""

    def __init__(
        self,
        order_id,
        username,
        product_id,
        product_name,
        quantity,
        total_price,
        status="已下单"
    ):
        # 订单编号，用来唯一标识一个订单
        self.order_id = order_id

        # 下单用户名，表示是谁购买了商品
        self.username = username

        # 商品编号，表示购买的是哪个商品
        self.product_id = product_id

        # 商品名称，方便查看订单时显示
        self.product_name = product_name

        # 购买数量
        self.quantity = quantity

        # 订单总价，等于商品价格乘以购买数量
        self.total_price = total_price

        # 订单状态，例如：已下单、已支付、已发货、已完成
        self.status = status

    def to_dict(self):
        """将订单对象转换成字典，方便保存到 JSON 文件。"""
        return {
            "order_id": self.order_id,
            "username": self.username,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "total_price": self.total_price,
            "status": self.status
        }
