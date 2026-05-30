class Product:
    """商品类，用来保存商品的基本信息。"""

    def __init__(self, product_id, name, price, stock, image_path=""):
        # 商品编号，用来唯一标识一个商品
        self.product_id = product_id

        # 商品名称
        self.name = name

        # 商品价格
        self.price = price

        # 商品库存数量
        self.stock = stock

        # 商品图片路径，用来在网页中显示商品图片
        self.image_path = image_path

    def to_dict(self):
        """将商品对象转换成字典，方便保存到 JSON 文件。"""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "image_path": self.image_path
        }
