import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL", "sqlite:///users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }


def json_error(message, status_code):
    return jsonify({"error": message}), status_code


@app.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "service": "users"})
    except Exception:
        return jsonify({"status": "error", "service": "users"}), 503


@app.get("/users")
def list_users():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify([user.to_dict() for user in users])


@app.get("/users/<int:user_id>")
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return json_error("User not found", 404)
    return jsonify(user.to_dict())


@app.post("/users")
def create_user():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not username or not email or not password:
        return json_error("username, email and password are required", 400)
    if len(password) < 6:
        return json_error("password must contain at least 6 characters", 400)

    if User.query.filter_by(email=email).first():
        return json_error("email already exists", 409)

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@app.put("/users/<int:user_id>")
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return json_error("User not found", 404)

    payload = request.get_json(silent=True) or {}

    if "username" in payload:
        username = (payload.get("username") or "").strip()
        if not username:
            return json_error("username cannot be empty", 400)
        user.username = username

    if "email" in payload:
        email = (payload.get("email") or "").strip().lower()
        if not email:
            return json_error("email cannot be empty", 400)
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            return json_error("email already exists", 409)
        user.email = email

    if "password" in payload:
        password = payload.get("password") or ""
        if len(password) < 6:
            return json_error("password must contain at least 6 characters", 400)
        user.password_hash = generate_password_hash(password)

    db.session.commit()
    return jsonify(user.to_dict())


@app.delete("/users/<int:user_id>")
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return json_error("User not found", 404)
    db.session.delete(user)
    db.session.commit()
    return "", 204


@app.post("/users/login")
def login_user():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return json_error("email and password are required", 400)

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return json_error("invalid credentials", 401)

    return jsonify({"message": "login successful", "user": user.to_dict()})


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
