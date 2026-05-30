import json
import os
import uuid

from flask import (
    Flask,
    flash,
    has_request_context,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from order import Order
from product import Product
from user import User


# 创建 Flask 应用对象
app = Flask(__name__)

# session 需要密钥，初学阶段先写在代码中，后续项目可以放到配置文件
app.secret_key = "ecommerce-admin-secret-key"

# 商品数据文件路径，继续使用原来的 products.json
PRODUCTS_FILE = os.path.join("data", "products.json")

# 用户数据文件路径，继续使用原来的 users.json
USERS_FILE = os.path.join("data", "users.json")

# 订单数据文件路径，继续使用原来的 orders.json
ORDERS_FILE = os.path.join("data", "orders.json")

# 购物车数据文件路径，继续使用原来的 carts.json
CARTS_FILE = os.path.join("data", "carts.json")

# 商品图片上传目录
UPLOAD_FOLDER = os.path.join("static", "uploads")

# 允许上传的图片扩展名
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# 确保图片上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_users():
    """从 users.json 文件中读取用户列表。"""
    return read_json_file(USERS_FILE, "用户")


def save_users(users):
    """将用户列表保存到 users.json 文件。"""
    return save_json_file(USERS_FILE, users, "用户")


def load_products():
    """从 products.json 文件中读取商品列表。"""
    return read_json_file(PRODUCTS_FILE, "商品")


def save_products(products):
    """将商品列表保存到 products.json 文件。"""
    return save_json_file(PRODUCTS_FILE, products, "商品")


def load_orders():
    """从 orders.json 文件中读取订单列表。"""
    return read_json_file(ORDERS_FILE, "订单")


def save_orders(orders):
    """将订单列表保存到 orders.json 文件。"""
    return save_json_file(ORDERS_FILE, orders, "订单")


def load_carts():
    """从 carts.json 文件中读取购物车列表。"""
    return read_json_file(CARTS_FILE, "购物车")


def save_carts(carts):
    """将购物车列表保存到 carts.json 文件。"""
    return save_json_file(CARTS_FILE, carts, "购物车")


def show_friendly_error(message):
    """在 Web 请求中显示友好错误提示，避免把异常直接暴露给用户。"""
    if has_request_context():
        flash(message, "danger")


def read_json_file(file_path, data_name):
    """安全读取 JSON 文件，读取失败时返回空列表并给出友好提示。"""
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        show_friendly_error(f"{data_name}数据文件格式错误，请检查 JSON 文件。")
        return []
    except OSError:
        show_friendly_error(f"{data_name}数据读取失败，请稍后重试。")
        return []

    if not isinstance(data, list):
        show_friendly_error(f"{data_name}数据格式不正确，应为列表。")
        return []

    return data


def save_json_file(file_path, data, data_name):
    """安全保存 JSON 文件，保存失败时给出友好提示。"""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except OSError:
        show_friendly_error(f"{data_name}数据保存失败，请稍后重试。")
        return False

    return True


def is_allowed_image(filename):
    """判断上传文件是否为允许的图片类型。"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def save_product_image(image_file):
    """保存商品图片，并返回可以写入 JSON 的相对路径。"""
    if image_file is None or image_file.filename == "":
        return ""

    if not is_allowed_image(image_file.filename):
        return None

    # 使用安全文件名和随机前缀，避免文件名冲突和路径风险
    filename = secure_filename(image_file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    image_file.save(save_path)

    return os.path.join("uploads", unique_filename).replace("\\", "/")


def delete_product_image(image_path):
    """删除商品图片，只允许删除 static/uploads 目录中的文件。"""
    if not image_path:
        return

    upload_dir = os.path.abspath(UPLOAD_FOLDER)
    image_file_path = os.path.abspath(os.path.join("static", image_path))

    # 确认文件路径位于上传目录内，避免误删其他文件
    if os.path.commonpath([upload_dir, image_file_path]) != upload_dir:
        return

    if os.path.exists(image_file_path):
        os.remove(image_file_path)


def check_user_password(saved_password, input_password):
    """验证用户密码，兼容旧版本明文密码和新版本哈希密码。"""
    try:
        return check_password_hash(saved_password, input_password)
    except ValueError:
        # 旧数据可能是明文密码，这里保留兼容，避免已有用户无法登录
        return saved_password == input_password


def is_password_hash(saved_password):
    """判断当前密码是否已经是 Werkzeug 生成的哈希值。"""
    return (
        saved_password.startswith("scrypt:")
        or saved_password.startswith("pbkdf2:")
    )


def get_current_user():
    """从 session 中获取当前登录用户名。"""
    return session.get("username")


def is_admin(username):
    """判断当前用户是否为管理员。"""
    users = load_users()

    for user in users:
        if user["username"] == username and user.get("role") == "admin":
            return True

    return False


def get_user_role(username):
    """根据用户名获取用户角色，旧用户没有 role 时默认是普通用户。"""
    users = load_users()

    for user in users:
        if user["username"] == username:
            return user.get("role", "user")

    return "user"


def get_current_role():
    """获取当前登录用户角色，未登录时返回 None。"""
    username = get_current_user()

    if username is None:
        return None

    return get_user_role(username)


def require_login():
    """检查用户是否已经登录，未登录时返回 False。"""
    if get_current_user() is None:
        flash("请先登录。", "danger")
        return False

    return True


def require_admin():
    """检查当前用户是否为管理员，普通用户访问时提示权限不足。"""
    if not require_login():
        return False

    if get_current_role() != "admin":
        flash("权限不足。", "danger")
        return False

    return True


def initialize_users():
    """系统启动时补齐用户角色，并确保默认管理员账号存在。"""
    users = load_users()
    changed = False
    has_admin = False

    for user in users:
        # 旧用户没有 role 字段时，默认设置为普通用户
        if "role" not in user:
            user["role"] = "user"
            changed = True

        if user["username"] == "admin":
            has_admin = True
            if user.get("role") != "admin":
                user["role"] = "admin"
                changed = True

            # 默认管理员密码如果还是明文，也升级为哈希
            if not is_password_hash(user["password"]):
                user["password"] = generate_password_hash(user["password"])
                changed = True

    if not has_admin:
        # 没有管理员时自动创建默认管理员：admin / admin123
        admin_user = User(
            "admin",
            generate_password_hash("admin123"),
            "admin"
        )
        users.append(admin_user.to_dict())
        changed = True

    if changed:
        save_users(users)


@app.context_processor
def inject_current_user():
    """向所有模板注入当前用户名和角色，方便导航栏判断显示。"""
    return {
        "current_username": get_current_user(),
        "current_role": get_current_role()
    }


@app.route("/")
def index():
    """首页，显示系统名称和功能入口。"""
    username = get_current_user()
    return render_template("index.html", username=username)


@app.route("/register", methods=["GET", "POST"])
def register():
    """注册页面，GET 显示表单，POST 保存用户。"""
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            message = "请输入用户名和密码。"
            return render_template("register.html", message=message)

        users = load_users()

        # 注册前检查用户名是否已经存在
        for user in users:
            if user["username"] == username:
                message = "用户名已存在，注册失败。"
                return render_template("register.html", message=message)

        # 注册时使用哈希密码，避免明文保存密码
        hashed_password = generate_password_hash(password)
        # 新注册用户默认为普通用户
        new_user = User(username, hashed_password, "user")
        users.append(new_user.to_dict())
        if not save_users(users):
            message = "注册失败，用户数据保存异常。"
            return render_template("register.html", message=message)

        flash("注册成功，请登录。", "success")
        return redirect(url_for("login"))

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    """登录页面，登录成功后将用户名保存到 session。"""
    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()

        for user in users:
            if user["username"] == username and check_user_password(user["password"], password):
                # 旧明文密码登录成功后，自动升级为哈希密码保存
                if not is_password_hash(user["password"]):
                    user["password"] = generate_password_hash(password)
                    save_users(users)

                # 使用 session 记录当前登录用户
                session["username"] = username
                session["role"] = user.get("role", "user")
                flash("登录成功。", "success")
                return redirect(url_for("index"))

        message = "用户名或密码错误，登录失败。"

    return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    """退出登录，清除 session 中的用户名。"""
    session.pop("username", None)
    session.pop("role", None)
    flash("已退出登录。", "success")
    return redirect(url_for("index"))


@app.route("/products")
def products():
    """商品列表页面。"""
    product_list = load_products()
    return render_template("products.html", products=product_list)


@app.route("/products/<product_id>")
def product_detail(product_id):
    """商品详情页面，显示商品大图和详细信息。"""
    products_data = load_products()

    for product in products_data:
        if product["product_id"] == product_id:
            return render_template("product_detail.html", product=product)

    flash("商品不存在。", "danger")
    return redirect(url_for("products"))


@app.route("/cart/add/<product_id>", methods=["POST"])
def add_to_cart(product_id):
    """将商品加入购物车，必须登录后才能使用。"""
    if not require_login():
        return redirect(url_for("login"))

    username = get_current_user()
    products_data = load_products()
    carts_data = load_carts()

    for product in products_data:
        if product["product_id"] == product_id:
            if product["stock"] <= 0:
                flash("商品库存不足，无法加入购物车。", "danger")
                return redirect(url_for("products"))

            # 如果购物车中已经有同一商品，则数量加 1
            for cart_item in carts_data:
                if (
                    cart_item["username"] == username
                    and cart_item["product_id"] == product_id
                ):
                    if cart_item["quantity"] >= product["stock"]:
                        flash("购物车数量已达到商品库存上限。", "danger")
                        return redirect(url_for("products"))

                    cart_item["quantity"] = cart_item["quantity"] + 1
                    save_carts(carts_data)
                    flash("商品已加入购物车。", "success")
                    return redirect(url_for("products"))

            # 创建新的购物车商品记录
            carts_data.append({
                "username": username,
                "product_id": product["product_id"],
                "product_name": product["name"],
                "price": product["price"],
                "quantity": 1
            })
            save_carts(carts_data)
            flash("商品已加入购物车。", "success")
            return redirect(url_for("products"))

    flash("商品不存在，加入购物车失败。", "danger")
    return redirect(url_for("products"))


@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    """新增商品页面，GET 显示表单，POST 保存商品。"""
    if not require_admin():
        return redirect(url_for("products"))

    message = ""

    if request.method == "POST":
        product_id = request.form.get("product_id")
        name = request.form.get("name")
        price_text = request.form.get("price")
        stock_text = request.form.get("stock")
        image_file = request.files.get("image")

        if not product_id or not name or not price_text or not stock_text:
            message = "请填写完整的商品信息。"
            return render_template("add_product.html", message=message)

        try:
            price = float(price_text)
            stock = int(stock_text)
        except ValueError:
            message = "价格或库存格式错误。"
            return render_template("add_product.html", message=message)

        products_data = load_products()

        # 检查商品编号是否已经存在
        for product in products_data:
            if product["product_id"] == product_id:
                message = "商品编号已存在，添加失败。"
                return render_template("add_product.html", message=message)

        # 保存上传的商品图片
        image_path = save_product_image(image_file)
        if image_path is None:
            message = "图片格式不支持，请上传 png、jpg、jpeg、gif 或 webp 图片。"
            return render_template("add_product.html", message=message)

        # 创建商品对象，并转换成字典保存到 JSON 文件
        new_product = Product(product_id, name, price, stock, image_path)
        products_data.append(new_product.to_dict())
        if not save_products(products_data):
            message = "商品保存失败，请稍后重试。"
            return render_template("add_product.html", message=message)

        flash("商品添加成功。", "success")
        return redirect(url_for("products"))

    return render_template("add_product.html", message=message)


@app.route("/products/delete/<product_id>", methods=["POST"])
def delete_product(product_id):
    """删除商品，并同步删除商品图片。"""
    if not require_admin():
        return redirect(url_for("products"))

    products_data = load_products()

    for product in products_data:
        if product["product_id"] == product_id:
            products_data.remove(product)

            if not save_products(products_data):
                flash("商品删除失败，请稍后重试。", "danger")
                return redirect(url_for("products"))

            # 商品数据删除成功后，再删除对应图片文件
            delete_product_image(product.get("image_path", ""))
            flash("商品删除成功。", "success")
            return redirect(url_for("products"))

    flash("商品不存在，删除失败。", "danger")
    return redirect(url_for("products"))


@app.route("/products/edit/<product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    """管理员修改商品信息和商品图片。"""
    if not require_admin():
        return redirect(url_for("products"))

    products_data = load_products()
    current_product = None

    for product in products_data:
        if product["product_id"] == product_id:
            current_product = product
            break

    if current_product is None:
        flash("商品不存在。", "danger")
        return redirect(url_for("products"))

    message = ""

    if request.method == "POST":
        name = request.form.get("name")
        price_text = request.form.get("price")
        stock_text = request.form.get("stock")
        image_file = request.files.get("image")

        if not name or not price_text or not stock_text:
            message = "请填写完整的商品信息。"
            return render_template(
                "edit_product.html",
                product=current_product,
                message=message
            )

        try:
            price = float(price_text)
            stock = int(stock_text)
        except ValueError:
            message = "价格或库存格式错误。"
            return render_template(
                "edit_product.html",
                product=current_product,
                message=message
            )

        new_image_path = save_product_image(image_file)
        if new_image_path is None:
            message = "图片格式不支持，请上传 png、jpg、jpeg、gif 或 webp 图片。"
            return render_template(
                "edit_product.html",
                product=current_product,
                message=message
            )

        old_image_path = current_product.get("image_path", "")
        current_product["name"] = name
        current_product["price"] = price
        current_product["stock"] = stock

        # 如果上传了新图片，则替换旧图片
        if new_image_path:
            current_product["image_path"] = new_image_path

        if not save_products(products_data):
            message = "商品保存失败，请稍后重试。"
            return render_template(
                "edit_product.html",
                product=current_product,
                message=message
            )

        if new_image_path:
            delete_product_image(old_image_path)

        flash("商品修改成功。", "success")
        return redirect(url_for("products"))

    return render_template(
        "edit_product.html",
        product=current_product,
        message=message
    )


@app.route("/cart")
def cart():
    """购物车页面，用户只能查看自己的购物车商品。"""
    if not require_login():
        return redirect(url_for("login"))

    username = get_current_user()
    carts_data = load_carts()
    cart_items = []

    # 只显示当前用户自己的购物车商品
    for cart_item in carts_data:
        if cart_item["username"] == username:
            cart_items.append(cart_item)

    total_price = 0
    for item in cart_items:
        total_price = total_price + item["price"] * item["quantity"]

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_price=total_price
    )


@app.route("/cart/delete/<int:item_index>", methods=["POST"])
def delete_cart_item(item_index):
    """删除当前用户购物车中的一个商品。"""
    if not require_login():
        return redirect(url_for("login"))

    username = get_current_user()
    carts_data = load_carts()
    user_item_indexes = []

    # 找出当前用户购物车商品在完整购物车列表中的真实下标
    for index, cart_item in enumerate(carts_data):
        if cart_item["username"] == username:
            user_item_indexes.append(index)

    if item_index < 0 or item_index >= len(user_item_indexes):
        flash("购物车商品不存在，删除失败。", "danger")
        return redirect(url_for("cart"))

    real_index = user_item_indexes[item_index]
    carts_data.pop(real_index)

    if not save_carts(carts_data):
        flash("购物车保存失败，请稍后重试。", "danger")
        return redirect(url_for("cart"))

    flash("购物车商品已删除。", "success")
    return redirect(url_for("cart"))


@app.route("/cart/checkout", methods=["POST"])
def checkout_cart():
    """将当前用户购物车中的商品一键生成订单。"""
    if not require_login():
        return redirect(url_for("login"))

    username = get_current_user()
    carts_data = load_carts()
    products_data = load_products()
    orders_data = load_orders()

    user_cart_items = []
    for cart_item in carts_data:
        if cart_item["username"] == username:
            user_cart_items.append(cart_item)

    if len(user_cart_items) == 0:
        flash("购物车为空，无法生成订单。", "danger")
        return redirect(url_for("cart"))

    # 先检查所有商品是否存在且库存足够，避免只生成部分订单
    for cart_item in user_cart_items:
        matched_product = None

        for product in products_data:
            if product["product_id"] == cart_item["product_id"]:
                matched_product = product
                break

        if matched_product is None:
            flash(f"商品 {cart_item['product_name']} 不存在，结算失败。", "danger")
            return redirect(url_for("cart"))

        if matched_product["stock"] < cart_item["quantity"]:
            flash(f"商品 {cart_item['product_name']} 库存不足，结算失败。", "danger")
            return redirect(url_for("cart"))

    # 库存检查通过后，扣减库存并生成订单
    for cart_item in user_cart_items:
        for product in products_data:
            if product["product_id"] == cart_item["product_id"]:
                product["stock"] = product["stock"] - cart_item["quantity"]
                break

        order_id = str(len(orders_data) + 1)
        total_price = cart_item["price"] * cart_item["quantity"]

        new_order = Order(
            order_id,
            username,
            cart_item["product_id"],
            cart_item["product_name"],
            cart_item["quantity"],
            total_price
        )
        orders_data.append(new_order.to_dict())

    # 结算成功后，清空当前用户的购物车
    remaining_cart_items = []
    for cart_item in carts_data:
        if cart_item["username"] != username:
            remaining_cart_items.append(cart_item)

    if not save_orders(orders_data):
        flash("订单保存失败，请稍后重试。", "danger")
        return redirect(url_for("cart"))

    if not save_products(products_data):
        flash("商品库存保存失败，请稍后重试。", "danger")
        return redirect(url_for("cart"))

    if not save_carts(remaining_cart_items):
        flash("购物车保存失败，请稍后重试。", "danger")
        return redirect(url_for("cart"))

    flash("购物车已成功生成订单。", "success")
    return redirect(url_for("orders"))


@app.route("/orders")
def orders():
    """订单列表页面，普通用户只看自己的订单，管理员看全部订单。"""
    username = get_current_user()

    if username is None:
        flash("请先登录。", "danger")
        return redirect(url_for("login"))

    all_orders = load_orders()

    # 管理员可以查看全部订单，普通用户只能查看自己的订单
    if is_admin(username):
        order_list = all_orders
    else:
        order_list = []
        for order in all_orders:
            if order["username"] == username:
                order_list.append(order)

    return render_template("orders.html", orders=order_list, username=username)


@app.route("/orders/status/<order_id>", methods=["POST"])
def update_order_status(order_id):
    """管理员修改订单状态。"""
    if not require_admin():
        return redirect(url_for("orders"))

    new_status = request.form.get("status")
    orders_data = load_orders()

    if not new_status:
        flash("请选择订单状态。", "danger")
        return redirect(url_for("orders"))

    for order in orders_data:
        if order["order_id"] == order_id:
            order["status"] = new_status

            if not save_orders(orders_data):
                flash("订单状态保存失败，请稍后重试。", "danger")
                return redirect(url_for("orders"))

            flash("订单状态修改成功。", "success")
            return redirect(url_for("orders"))

    flash("订单不存在。", "danger")
    return redirect(url_for("orders"))


@app.route("/users")
def users():
    """管理员查看所有用户。"""
    if not require_admin():
        return redirect(url_for("index"))

    user_list = load_users()
    return render_template("users.html", users=user_list)


@app.route("/orders/add", methods=["GET", "POST"])
def add_order():
    """用户下单页面，未登录用户不能下单。"""
    username = get_current_user()

    if username is None:
        flash("请先登录。", "danger")
        return redirect(url_for("login"))

    message = ""
    products_data = load_products()

    if request.method == "POST":
        product_id = request.form.get("product_id")
        quantity_text = request.form.get("quantity")

        try:
            quantity = int(quantity_text)
        except (TypeError, ValueError):
            message = "购买数量格式错误。"
            return render_template(
                "add_order.html",
                products=products_data,
                message=message
            )

        if quantity <= 0:
            message = "购买数量必须大于 0。"
            return render_template(
                "add_order.html",
                products=products_data,
                message=message
            )

        for product in products_data:
            if product["product_id"] == product_id:
                if product["stock"] < quantity:
                    message = "商品库存不足，下单失败。"
                    return render_template(
                        "add_order.html",
                        products=products_data,
                        message=message
                    )

                # 计算总价并扣减库存
                total_price = product["price"] * quantity
                product["stock"] = product["stock"] - quantity

                orders_data = load_orders()
                order_id = str(len(orders_data) + 1)

                # 创建订单对象，并保存到 orders.json
                new_order = Order(
                    order_id,
                    username,
                    product["product_id"],
                    product["name"],
                    quantity,
                    total_price
                )
                orders_data.append(new_order.to_dict())

                if not save_orders(orders_data):
                    message = "订单保存失败，请稍后重试。"
                    return render_template(
                        "add_order.html",
                        products=products_data,
                        message=message
                    )

                if not save_products(products_data):
                    message = "商品库存保存失败，请稍后重试。"
                    return render_template(
                        "add_order.html",
                        products=products_data,
                        message=message
                    )

                flash("下单成功。", "success")
                return redirect(url_for("orders"))

        message = "商品不存在，下单失败。"

    return render_template(
        "add_order.html",
        products=products_data,
        message=message
    )


@app.errorhandler(404)
def page_not_found(error):
    """404 错误页面，访问不存在的地址时显示。"""
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    """500 错误页面，服务器内部错误时显示。"""
    return render_template("500.html"), 500


# 程序启动时初始化用户角色和默认管理员账号
initialize_users()


if __name__ == "__main__":
    # 启动 Flask Web 项目，运行方式：python app.py
    app.run(debug=True)
