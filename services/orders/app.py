import os
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL", "sqlite:///orders.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL", "http://products:5002").rstrip("/")
ALLOWED_STATUSES = {"created", "validated", "cancelled"}

db = SQLAlchemy(app)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(40), nullable=False, default="created")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_price": round(float(self.total_price), 2),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


def json_error(message, status_code):
    return jsonify({"error": message}), status_code


@app.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "service": "orders"})
    except Exception:
        return jsonify({"status": "error", "service": "orders"}), 503


@app.get("/orders")
def list_orders():
    orders = Order.query.order_by(Order.id.asc()).all()
    return jsonify([order.to_dict() for order in orders])


@app.get("/orders/<int:order_id>")
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return json_error("Order not found", 404)
    return jsonify(order.to_dict())


@app.get("/orders/user/<int:user_id>")
def get_orders_by_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.asc()).all()
    return jsonify([order.to_dict() for order in orders])


@app.post("/orders")
def create_order():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    product_id = payload.get("product_id")
    quantity = payload.get("quantity")

    if not isinstance(user_id, int) or user_id <= 0:
        return json_error("user_id must be an integer > 0", 400)
    if not isinstance(product_id, int) or product_id <= 0:
        return json_error("product_id must be an integer > 0", 400)
    if not isinstance(quantity, int) or quantity <= 0:
        return json_error("quantity must be an integer > 0", 400)

    product_url = f"{PRODUCTS_SERVICE_URL}/products/{product_id}"
    reserve_url = f"{PRODUCTS_SERVICE_URL}/products/{product_id}/reserve"

    try:
        product_response = requests.get(product_url, timeout=5)
    except requests.RequestException:
        return json_error("products service unavailable", 503)

    if product_response.status_code == 404:
        return json_error("product not found", 404)
    if product_response.status_code >= 500:
        return json_error("products service error", 503)
    if product_response.status_code != 200:
        return json_error("unable to validate product", 502)

    product_data = product_response.json()
    current_stock = product_data.get("stock", 0)
    if current_stock < quantity:
        return json_error("insufficient stock", 409)

    try:
        reserve_response = requests.post(reserve_url, json={"quantity": quantity}, timeout=5)
    except requests.RequestException:
        return json_error("products service unavailable", 503)

    if reserve_response.status_code == 409:
        return json_error("insufficient stock", 409)
    if reserve_response.status_code == 404:
        return json_error("product not found", 404)
    if reserve_response.status_code >= 500:
        return json_error("products service error", 503)
    if reserve_response.status_code != 200:
        return json_error("unable to reserve product stock", 502)

    reserve_data = reserve_response.json()
    total_price = float(reserve_data.get("total_price", 0.0))

    order = Order(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
        total_price=total_price,
        status="created",
    )
    db.session.add(order)
    db.session.commit()

    return jsonify(order.to_dict()), 201


@app.put("/orders/<int:order_id>")
def update_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return json_error("Order not found", 404)

    payload = request.get_json(silent=True) or {}

    if "status" in payload:
        status = (payload.get("status") or "").strip().lower()
        if status not in ALLOWED_STATUSES:
            return json_error("status must be one of created, validated, cancelled", 400)
        order.status = status

    db.session.commit()
    return jsonify(order.to_dict())


@app.delete("/orders/<int:order_id>")
def delete_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return json_error("Order not found", 404)

    db.session.delete(order)
    db.session.commit()
    return "", 204


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
