import os
import psycopg2
import psycopg2.extras
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

PRODUCTS_SERVICE_URL = "http://localhost:5002"

def get_db():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "orders-db"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "orders"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres")
    )

def init_db():
    """Initialize the database schema."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price DECIMAL(10,2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/health", methods=["GET"])
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route("/orders", methods=["GET"])
def get_orders():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM orders ORDER BY id")
    orders = cur.fetchall()
    cur.close()
    conn.close()
    for o in orders:
        o["total_price"] = float(o["total_price"])
        o["created_at"] = o["created_at"].isoformat() if o["created_at"] else None
    return jsonify(orders), 200

@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    cur.close()
    conn.close()
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    order["total_price"] = float(order["total_price"])
    order["created_at"] = order["created_at"].isoformat() if order["created_at"] else None
    return jsonify(order), 200

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    if not data or not all(k in data for k in ("user_id", "product_id", "quantity")):
        return jsonify({"error": "Missing required fields: user_id, product_id, quantity"}), 400

    quantity = int(data["quantity"])
    if quantity <= 0:
        return jsonify({"error": "Quantity must be positive"}), 400

    # Verify product exists and has sufficient stock
    try:
        product_resp = requests.get(f"{PRODUCTS_SERVICE_URL}/products/{data['product_id']}")
    except requests.ConnectionError:
        return jsonify({"error": "Products service unavailable"}), 503

    if product_resp.status_code == 404:
        return jsonify({"error": "Product not found"}), 404
    if product_resp.status_code != 200:
        return jsonify({"error": "Failed to fetch product"}), 500

    product = product_resp.json()

    if product["stock"] < quantity:
        return jsonify({"error": "Insufficient stock", "available": product["stock"]}), 400

    total_price = float(product["price"]) * quantity

    # Decrement stock
    new_stock = product["stock"] - quantity
    update_resp = requests.put(
        f"{PRODUCTS_SERVICE_URL}/products/{data['product_id']}",
        json={"stock": new_stock}
    )
    if update_resp.status_code != 200:
        return jsonify({"error": "Failed to update product stock"}), 500

    # Create the order
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "INSERT INTO orders (user_id, product_id, quantity, total_price, status) VALUES (%s, %s, %s, %s, %s) RETURNING *",
        (data["user_id"], data["product_id"], quantity, total_price, "confirmed")
    )
    order = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    order["total_price"] = float(order["total_price"])
    order["created_at"] = order["created_at"].isoformat() if order["created_at"] else None
    return jsonify(order), 201

@app.route("/orders/user/<int:user_id>", methods=["GET"])
def get_user_orders(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY id", (user_id,))
    orders = cur.fetchall()
    cur.close()
    conn.close()
    for o in orders:
        o["total_price"] = float(o["total_price"])
        o["created_at"] = o["created_at"].isoformat() if o["created_at"] else None
    return jsonify(orders), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5003)
