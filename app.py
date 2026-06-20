from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "nhaboi123"

# ==========================
# KHỞI TẠO DATABASE
# ==========================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # PRODUCTS
    c.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        category TEXT
    )
    """)

    # ORDERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        product_name TEXT,
        price INTEGER
    )
    """)

    # Cập nhật thêm các cột mới vào bảng orders (Bao gồm completed_at)
    columns = [
        ("full_name", "TEXT"),
        ("phone", "TEXT"),
        ("address", "TEXT"),
        ("status", "TEXT DEFAULT 'Chờ xử lý'"),
        ("created_at", "TEXT"),
        ("completed_at", "TEXT")
    ]
    for col_name, col_type in columns:
        try:
            c.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
        except:
            pass

    # Tạo tài khoản admin
    try:
        c.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            ("admin", "123456")
        )
    except:
        pass

    # Thêm menu lần đầu
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            ("Trà tắc", 10000, "Trà"), ("Trà chanh", 10000, "Trà"), ("Trà tắc thái xanh", 10000, "Trà"),
            ("Trà chanh thái xanh", 15000, "Trà"), ("Trà tắc xí muội", 15000, "Trà"), ("Trà me hạt dẻo", 20000, "Trà"),
            ("Trà chanh dây", 15000, "Trà trái cây"), ("Trà việt quất", 15000, "Trà trái cây"),
            ("Trà ổi hồng", 18000, "Trà trái cây"), ("Trà dâu tằm", 15000, "Trà trái cây"),
            ("Trà vải", 20000, "Trà trái cây"), ("Trà đào", 15000, "Trà trái cây"),
            ("Trà sữa truyền thống", 15000, "Trà sữa"), ("Trà sữa thái xanh", 15000, "Trà sữa"),
            ("Trà sữa khoai môn", 18000, "Trà sữa"), ("Trà sữa gạo rang", 18000, "Trà sữa"),
            ("Trà sữa socola", 25000, "Trà sữa"), ("Trà sữa caramel", 25000, "Trà sữa"), ("Trà sữa phô mai", 30000, "Trà sữa"),
            ("Matcha Latte", 18000, "Latte"), ("Khoai môn Latte", 18000, "Latte"), ("Cacao Latte", 18000, "Latte"),
            ("Matcha đào", 19000, "Latte"), ("Coco Matcha", 28000, "Latte"),
            ("Sữa chua nguyên vị", 23000, "Sữa chua"), ("Sữa chua việt quất", 25000, "Sữa chua"), ("Sữa chua đào", 25000, "Sữa chua"),
            ("Đá bào sữa", 10000, "Đá bào"), ("Milo dầm", 20000, "Đá bào"),
            ("Bánh tráng trộn", 15000, "Ăn vặt"), ("Khô gà", 90000, "Ăn vặt"), ("Tóp mỡ", 39000, "Ăn vặt")
        ]
        c.executemany("INSERT INTO products(name,price,category) VALUES (?,?,?)", products)

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template("index.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users(username,password) VALUES (?,?)", (username, password))
            conn.commit()
        except:
            conn.close()
            return "Tên đăng nhập đã tồn tại"
        conn.close()
        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["user"] = username
            return redirect("/")
        return "Sai tài khoản hoặc mật khẩu"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/add/<int:id>")
def add(id):
    if "user" not in session: return redirect("/login")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    product = c.fetchone()
    conn.close()
    if "cart" not in session: session["cart"] = []
    cart = session["cart"]
    cart.append({"name": product[1], "price": product[2]})
    session["cart"] = cart
    return redirect("/")


@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)
    return render_template("cart.html", cart=cart, total=total)


@app.route("/checkout", methods=["POST"])
def checkout():
    if "user" not in session: return redirect("/login")
    full_name = request.form["full_name"]
    phone = request.form["phone"]
    address = request.form["address"]
    cart = session.get("cart", [])
    
    # Lấy ngày giờ hiện tại cho thời gian ĐẶT hàng
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    for item in cart:
        c.execute("""
        INSERT INTO orders(username, full_name, phone, address, product_name, price, status, created_at)
        VALUES (?,?,?,?,?,?,?,?)
        """, (session["user"], full_name, phone, address, item["name"], item["price"], "Chờ xử lý", now))
    
    conn.commit()
    conn.close()
    session["cart"] = []
    return "<h1>Đặt hàng thành công 🎉</h1><a href='/'>Quay về trang chủ</a>"


# ==========================
# ADMIN QUẢN LÝ ĐƠN HÀNG
# ==========================
@app.route("/admin")
def admin():
    if "user" not in session: return redirect("/login")
    if session["user"] != "admin": return "Bạn không có quyền truy cập"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    # Lấy thêm cột completed_at (chỉ mục số 9 trong mảng trả về)
    c.execute("""
    SELECT id, username, full_name, phone, address, product_name, price, status, created_at, completed_at
    FROM orders ORDER BY id DESC
    """)
    orders = c.fetchall()
    conn.close()
    return render_template("admin.html", orders=orders)


@app.route("/admin/complete/<int:order_id>")
def complete_order(order_id):
    if session.get("user") != "admin": return redirect("/login")
    
    # Lấy ngày giờ hiện tại cho thời gian NHẬN (GIAO XONG) hàng
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE orders SET status = 'Hoàn thành', completed_at = ? WHERE id = ?", (now, order_id))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/admin/delete/<int:order_id>")
def delete_order(order_id):
    if session.get("user") != "admin": return redirect("/login")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)