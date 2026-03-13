import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "products-db"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "products"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres")
    )

def init_db():
    """Initialize the database schema."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
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

@app.route("/products", methods=["GET"])
def get_products():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM products ORDER BY id")
    products = cur.fetchall()
    cur.close()
    conn.close()
    for p in products:
        p["price"] = float(p["price"])
        p["created_at"] = p["created_at"].isoformat() if p["created_at"] else None
    return jsonify(products), 200

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    product["price"] = float(product["price"])
    product["created_at"] = product["created_at"].isoformat() if product["created_at"] else None
    return jsonify(product), 200

@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "price")):
        return jsonify({"error": "Missing required fields: name, price"}), 400

    stock = data.get("stock", 0)

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s) RETURNING *",
        (data["name"], data["price"], stock)
    )
    product = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    product["price"] = float(product["price"])
    product["created_at"] = product["created_at"].isoformat() if product["created_at"] else None
    return jsonify(product), 201

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    fields = []
    values = []
    if "name" in data:
        fields.append("name = %s")
        values.append(data["name"])
    if "price" in data:
        fields.append("price = %s")
        values.append(data["price"])
    if "stock" in data:
        fields.append("stock = %s")
        values.append(data["stock"])

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(product_id)
    query = f"UPDATE products SET {', '.join(fields)} WHERE id = %s RETURNING *"
    cur.execute(query, values)
    product = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if product is None:
        return jsonify({"error": "Product not found"}), 404
    product["price"] = float(product["price"])
    product["created_at"] = product["created_at"].isoformat() if product["created_at"] else None
    return jsonify(product), 200

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = %s RETURNING id", (product_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product deleted"}), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5002)
