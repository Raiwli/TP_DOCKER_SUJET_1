import os
import hashlib
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

def get_db():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "users-db"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "users"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres")
    )

def init_db():
    """Initialize the database schema."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
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

@app.route("/users", methods=["GET"])
def get_users():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, username, email, created_at FROM users ORDER BY id")
    users = cur.fetchall()
    cur.close()
    conn.close()
    # Convert datetime objects to strings
    for user in users:
        user["created_at"] = user["created_at"].isoformat() if user["created_at"] else None
    return jsonify(users), 200

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, username, email, created_at FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user is None:
        return jsonify({"error": "User not found"}), 404
    user["created_at"] = user["created_at"].isoformat() if user["created_at"] else None
    return jsonify(user), 200

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Missing required fields: username, email, password"}), 400

    password_hash = hashlib.sha256(data["password"].encode()).hexdigest()

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id, username, email, created_at",
            (data["username"], data["email"], password_hash)
        )
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        user["created_at"] = user["created_at"].isoformat() if user["created_at"] else None
        return jsonify(user), 201
    except psycopg2.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 409

@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Build dynamic update query
    fields = []
    values = []
    if "username" in data:
        fields.append("username = %s")
        values.append(data["username"])
    if "email" in data:
        fields.append("email = %s")
        values.append(data["email"])
    if "password" in data:
        fields.append("password_hash = %s")
        values.append(hashlib.sha256(data["password"].encode()).hexdigest())

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(user_id)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s RETURNING id, username, email, created_at"

    try:
        cur.execute(query, values)
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if user is None:
            return jsonify({"error": "User not found"}), 404
        user["created_at"] = user["created_at"].isoformat() if user["created_at"] else None
        return jsonify(user), 200
    except psycopg2.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 409

@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User deleted"}), 200

@app.route("/users/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "password")):
        return jsonify({"error": "Missing required fields: username, password"}), 400

    password_hash = hashlib.sha256(data["password"].encode()).hexdigest()

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id, username, email FROM users WHERE username = %s AND password_hash = %s",
        (data["username"], password_hash)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user is None:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"message": "Login successful", "user": user}), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001)
