import json
import os

from order import Order
from product import Product
from user import User
from werkzeug.security import check_password_hash, generate_password_hash


# 用户数据文件路径
USERS_FILE = os.path.join("data", "users.json")

# 商品数据文件路径
PRODUCTS_FILE = os.path.join("data", "products.json")

# 订单数据文件路径
ORDERS_FILE = os.path.join("data", "orders.json")

# 当前登录用户，None 表示没有用户登录
current_user = None


def load_users():
    """从 users.json 文件中读取用户列表。"""
    if not os.path.exists(USERS_FILE):
        return []

    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_users(users):
    """将用户列表保存到 users.json 文件。"""
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


def load_products():
    """从 products.json 文件中读取商品列表。"""
    if not os.path.exists(PRODUCTS_FILE):
        return []

    with open(PRODUCTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_products(products):
    """将商品列表保存到 products.json 文件。"""
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=4)


def load_orders():
    """从 orders.json 文件中读取订单列表。"""
    if not os.path.exists(ORDERS_FILE):
        return []

    with open(ORDERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_orders(orders):
    """将订单列表保存到 orders.json 文件。"""
    with open(ORDERS_FILE, "w", encoding="utf-8") as file:
        json.dump(orders, file, ensure_ascii=False, indent=4)


def check_user_password(saved_password, input_password):
    """验证用户密码，兼容旧明文密码和新哈希密码。"""
    try:
        return check_password_hash(saved_password, input_password)
    except ValueError:
        # 旧版本可能保存的是明文密码，这里保留兼容
        return saved_password == input_password


def is_password_hash(saved_password):
    """判断密码是否已经是 Werkzeug 生成的哈希值。"""
    return (
        saved_password.startswith("scrypt:")
        or saved_password.startswith("pbkdf2:")
    )


def is_admin(username):
    """判断当前用户是否为管理员。"""
    if username == "admin":
        return True

    users = load_users()

    for user in users:
        if user["username"] == username and user.get("role") == "admin":
            return True

    return False


def register_user():
    """用户注册功能。"""
    username = input("请输入用户名：")
    password = input("请输入密码：")

    users = load_users()

    for user in users:
        if user["username"] == username:
            print("用户名已存在，注册失败。")
            return

    # 注册时保存哈希密码，避免明文保存密码
    hashed_password = generate_password_hash(password)
    new_user = User(username, hashed_password)
    users.append(new_user.to_dict())
    save_users(users)
    print("注册成功！")


def login_user():
    """用户登录功能。"""
    global current_user

    username = input("请输入用户名：")
    password = input("请输入密码：")

    users = load_users()

    for user in users:
        if user["username"] == username and check_user_password(user["password"], password):
            # 旧明文密码登录成功后，自动升级为哈希密码保存
            if not is_password_hash(user["password"]):
                user["password"] = generate_password_hash(password)
                save_users(users)

            # 登录成功后，记录当前登录用户
            current_user = username
            print("登录成功！")
            return

    print("用户名或密码错误，登录失败。")


def logout_user():
    """退出登录功能。"""
    global current_user

    if current_user is None:
        print("当前没有用户登录。")
        return

    # 清空当前登录用户，表示已经退出登录
    print("用户", current_user, "已退出登录。")
    current_user = None


def show_user_menu():
    """显示用户管理菜单。"""
    print("===== 用户管理 =====")
    print("1. 用户注册")
    print("2. 用户登录")
    print("3. 返回上一菜单")


def user_menu():
    """用户管理菜单。"""
    while True:
        show_user_menu()
        choice = input("请输入菜单编号：")

        if choice == "1":
            register_user()
        elif choice == "2":
            login_user()
        elif choice == "3":
            print("返回上一菜单。")
            break
        else:
            print("输入错误，请重新选择。")

        print()


def show_all_products():
    """查看所有商品。"""
    products = load_products()

    if len(products) == 0:
        print("暂无商品。")
        return

    print("===== 商品列表 =====")
    for product in products:
        print("商品编号：", product["product_id"])
        print("商品名称：", product["name"])
        print("商品价格：", product["price"])
        print("商品库存：", product["stock"])
        print("--------------------")


def add_product():
    """添加商品。"""
    product_id = input("请输入商品编号：")
    name = input("请输入商品名称：")

    try:
        price = float(input("请输入商品价格："))
        stock = int(input("请输入商品库存："))
    except ValueError:
        print("价格或库存输入错误，添加失败。")
        return

    products = load_products()

    for product in products:
        if product["product_id"] == product_id:
            print("商品编号已存在，添加失败。")
            return

    new_product = Product(product_id, name, price, stock)
    products.append(new_product.to_dict())
    save_products(products)
    print("商品添加成功！")


def delete_product():
    """删除商品。"""
    product_id = input("请输入要删除的商品编号：")
    products = load_products()

    for product in products:
        if product["product_id"] == product_id:
            products.remove(product)
            save_products(products)
            print("商品删除成功！")
            return

    print("未找到该商品，删除失败。")


def update_product_price():
    """修改商品价格。"""
    product_id = input("请输入要修改价格的商品编号：")
    products = load_products()

    for product in products:
        if product["product_id"] == product_id:
            try:
                new_price = float(input("请输入新的商品价格："))
            except ValueError:
                print("价格输入错误，修改失败。")
                return

            product["price"] = new_price
            save_products(products)
            print("商品价格修改成功！")
            return

    print("未找到该商品，修改失败。")


def show_product_menu():
    """显示商品管理菜单。"""
    print("===== 商品管理 =====")
    print("1. 查看所有商品")
    print("2. 添加商品")
    print("3. 删除商品")
    print("4. 修改商品价格")
    print("5. 返回上一菜单")


def product_menu():
    """商品管理菜单。"""
    while True:
        show_product_menu()
        choice = input("请输入菜单编号：")

        if choice == "1":
            show_all_products()
        elif choice == "2":
            add_product()
        elif choice == "3":
            delete_product()
        elif choice == "4":
            update_product_price()
        elif choice == "5":
            print("返回上一菜单。")
            break
        else:
            print("输入错误，请重新选择。")

        print()


def create_order():
    """用户下单功能。"""
    if current_user is None:
        print("请先登录")
        return

    products = load_products()

    if len(products) == 0:
        print("暂无商品，无法下单。")
        return

    # 下单前先显示所有商品，方便用户选择商品编号
    show_all_products()

    product_id = input("请输入要购买的商品编号：")

    try:
        quantity = int(input("请输入购买数量："))
    except ValueError:
        print("购买数量输入错误，下单失败。")
        return

    if quantity <= 0:
        print("购买数量必须大于 0，下单失败。")
        return

    for product in products:
        if product["product_id"] == product_id:
            if product["stock"] < quantity:
                print("商品库存不足，下单失败。")
                return

            # 计算订单总价
            total_price = product["price"] * quantity

            # 扣减商品库存
            product["stock"] = product["stock"] - quantity

            # 订单编号使用当前订单数量加 1，方便初学者理解
            orders = load_orders()
            order_id = str(len(orders) + 1)

            # 创建订单对象
            new_order = Order(
                order_id,
                current_user,
                product["product_id"],
                product["name"],
                quantity,
                total_price
            )

            # 保存订单和最新商品库存
            orders.append(new_order.to_dict())
            save_orders(orders)
            save_products(products)

            print("下单成功！")
            print("订单编号：", order_id)
            print("订单总价：", total_price)
            return

    print("商品不存在，下单失败。")


def show_all_orders():
    """查看所有订单。"""
    if current_user is None:
        print("请先登录")
        return

    orders = load_orders()

    if len(orders) == 0:
        print("暂无订单。")
        return

    # 管理员可以查看所有订单，普通用户只能查看自己的订单
    if is_admin(current_user):
        user_orders = orders
    else:
        user_orders = []
        for order in orders:
            if order["username"] == current_user:
                user_orders.append(order)

    if len(user_orders) == 0:
        print("暂无订单。")
        return

    print("===== 订单列表 =====")
    for order in user_orders:
        print("订单编号：", order["order_id"])
        print("用户名：", order["username"])
        print("商品编号：", order["product_id"])
        print("商品名称：", order["product_name"])
        print("购买数量：", order["quantity"])
        print("订单总价：", order["total_price"])
        print("订单状态：", order["status"])
        print("--------------------")


def show_main_menu():
    """显示系统主菜单。"""
    if current_user is None:
        print("当前用户：未登录")
    else:
        print("当前用户：", current_user)

    print("===== 电商后台管理系统 =====")
    print("1. 用户管理")
    print("2. 商品管理")
    print("3. 管理员菜单")
    print("4. 用户下单")
    print("5. 查看订单")
    print("6. 退出登录")
    print("7. 退出系统")


def main():
    """程序主函数。"""
    while True:
        show_main_menu()
        choice = input("请输入菜单编号：")

        if choice == "1":
            user_menu()
        elif choice == "2":
            product_menu()
        elif choice == "3":
            print("管理员菜单功能暂未实现。")
        elif choice == "4":
            create_order()
        elif choice == "5":
            show_all_orders()
        elif choice == "6":
            logout_user()
        elif choice == "7":
            print("感谢使用，再见！")
            break
        else:
            print("输入错误，请重新选择。")

        print()


if __name__ == "__main__":
    main()
