import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

ALLOWED_SIZES = {"U9", "U12", "U15"}
MIN_PRICE = 1000.0

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL", "sqlite:///products.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "price": round(float(self.price), 2),
            "stock": self.stock,
            "created_at": self.created_at.isoformat(),
        }


def json_error(message, status_code):
    return jsonify({"error": message}), status_code


def validate_size(size):
    return size in ALLOWED_SIZES


def validate_price(price):
    try:
        return float(price) >= MIN_PRICE
    except (TypeError, ValueError):
        return False


def validate_stock(stock):
    return isinstance(stock, int) and stock >= 0


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@app.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "service": "products"})
    except Exception:
        return jsonify({"status": "error", "service": "products"}), 503


@app.get("/products")
def list_products():
    products = Product.query.order_by(Product.id.asc()).all()
    return jsonify([product.to_dict() for product in products])


@app.get("/products/<int:product_id>")
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return json_error("Product not found", 404)
    return jsonify(product.to_dict())


@app.post("/products")
def create_product():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    size = (payload.get("size") or "").strip().upper()
    price = payload.get("price")
    stock = payload.get("stock")

    if not name:
        return json_error("name is required", 400)
    if not validate_size(size):
        return json_error("size must be one of U9, U12, U15", 400)
    if not validate_price(price):
        return json_error("price must be >= 1000 EUR", 400)
    if not validate_stock(stock):
        return json_error("stock must be an integer >= 0", 400)

    price_value = to_float(price)
    stock_value = to_int(stock)
    if price_value is None or stock_value is None:
        return json_error("invalid price or stock", 400)
    product = Product(name=name, size=size, price=price_value, stock=stock_value)
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@app.put("/products/<int:product_id>")
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return json_error("Product not found", 404)

    payload = request.get_json(silent=True) or {}

    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            return json_error("name cannot be empty", 400)
        product.name = name

    if "size" in payload:
        size = (payload.get("size") or "").strip().upper()
        if not validate_size(size):
            return json_error("size must be one of U9, U12, U15", 400)
        product.size = size

    if "price" in payload:
        price = payload.get("price")
        if not validate_price(price):
            return json_error("price must be >= 1000 EUR", 400)
        parsed_price = to_float(price)
        if parsed_price is None:
            return json_error("invalid price", 400)
        product.price = parsed_price

    if "stock" in payload:
        stock = payload.get("stock")
        if not validate_stock(stock):
            return json_error("stock must be an integer >= 0", 400)
        parsed_stock = to_int(stock)
        if parsed_stock is None:
            return json_error("invalid stock", 400)
        product.stock = parsed_stock

    db.session.commit()
    return jsonify(product.to_dict())


@app.delete("/products/<int:product_id>")
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return json_error("Product not found", 404)
    db.session.delete(product)
    db.session.commit()
    return "", 204


@app.post("/products/<int:product_id>/reserve")
def reserve_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return json_error("Product not found", 404)

    payload = request.get_json(silent=True) or {}
    quantity = payload.get("quantity")
    if not isinstance(quantity, int) or quantity <= 0:
        return json_error("quantity must be an integer > 0", 400)

    if product.stock < quantity:
        return json_error("insufficient stock", 409)

    product.stock -= quantity
    db.session.commit()

    unit_price = round(float(product.price), 2)
    total_price = round(unit_price * quantity, 2)

    return jsonify(
        {
            "message": "stock reserved",
            "product_id": product.id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price,
            "remaining_stock": product.stock,
        }
    )


def seed_products_if_needed():
    if os.getenv("SEED_PRODUCTS", "true").lower() != "true":
        return
    if Product.query.count() > 0:
        return

    seeded = [
        Product(name="Kevin", size="U9", price=1299.90, stock=12),
        Product(name="Sophie", size="U12", price=2499.00, stock=10),
        Product(name="Nadia", size="U15", price=3999.50, stock=8),
        Product(name="Lucas", size="U9", price=1499.00, stock=15),
        Product(name="Emma", size="U12", price=2799.99, stock=9),
    ]
    db.session.add_all(seeded)
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_products_if_needed()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
