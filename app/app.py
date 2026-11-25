"""PulseGym member portal API.
A small Flask app used by the front desk and the member mobile app.
"""
import hashlib
import os
import sqlite3
import hmac
from functools import wraps

from flask import Flask, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# FIX: Removed hardcoded secret key, using environment variable
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-for-dev-only")
DB_PATH = os.environ.get("DB_PATH", "/data/pulsegym.db")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def hash_password(pw):
    # FIX: Use strong password hashing instead of MD5
    return generate_password_hash(pw)


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if "member_id" not in session:
            return jsonify(error="login required"), 401
        return fn(*a, **kw)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if session.get("role") != "admin":
            return jsonify(error="admins only"), 403
        return fn(*a, **kw)
    return login_required(wrapper)


@app.errorhandler(Exception)
def on_error(e):
    # FIX: Hide traceback and db path from users to prevent info disclosure
    app.logger.error(f"Error: {str(e)}")
    return jsonify(error="Internal Server Error"), 500


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/api/login")
def login():
    # EDGE CASE FIX: Use silent=True to handle invalid JSON gracefully
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Invalid JSON format"), 400
        
    row = db().execute("SELECT * FROM members WHERE email = ?", (body.get("email", ""),)).fetchone()
    # FIX: Use check_password_hash for secure comparison
    if not row or not check_password_hash(row["password_hash"], body.get("password", "")):
        return jsonify(error="wrong email or password"), 401
    session["member_id"], session["role"] = row["id"], row["role"]
    return jsonify(id=row["id"], name=row["name"], role=row["role"])


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(status="logged out")


@app.get("/api/members/<int:member_id>")
@login_required
def get_member(member_id):
    # FIX: Prevent IDOR.
    if member_id != session["member_id"] and session.get("role") != "admin":
        return jsonify(error="forbidden"), 403
        
    # FIX: Hide sensitive notes from non-admins
    query = "SELECT id, name, email, phone, plan, role, membership_paid FROM members WHERE id = ?"
    if session.get("role") == "admin":
        query = "SELECT id, name, email, phone, plan, role, membership_paid, notes FROM members WHERE id = ?"
        
    row = db().execute(query, (member_id,)).fetchone()
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))


@app.put("/api/members/<int:member_id>")
@login_required
def update_member(member_id):
    is_admin = session.get("role") == "admin"
    if member_id != session["member_id"] and not is_admin:
        return jsonify(error="you can only edit your own profile"), 403
    
    # EDGE CASE FIX: Use silent=True
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Invalid JSON format"), 400
    
    # FIX: Mass Assignment. Restrict which fields can be updated.
    allowed_fields = ["name", "phone", "email"]
    if is_admin:
        allowed_fields.extend(["role", "plan", "membership_paid"])
        
    fields = [k for k in body if k in allowed_fields]
    
    # EDGE CASE FIX: Handle IntegrityError for duplicate emails
    try:
        for k in fields:
            db().execute(f"UPDATE members SET {k} = ? WHERE id = ?", (body[k], member_id))
        db().commit()
    except sqlite3.IntegrityError:
        return jsonify(error="Email is already in use by another account"), 400
        
    if member_id == session["member_id"] and "role" in body and is_admin:
        session["role"] = body["role"]
    return get_member(member_id)


@app.get("/api/classes")
@login_required
def list_classes():
    search = request.args.get("search", "")
    # FIX: Parameterized query to prevent SQL Injection
    rows = db().execute("SELECT id, name, coach, starts_at, capacity FROM classes WHERE name LIKE ?", (f"%{search}%",)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/classes/<int:class_id>/book")
@login_required
def book(class_id):
    conn = db()
    cls = conn.execute("SELECT capacity FROM classes WHERE id = ?", (class_id,)).fetchone()
    if not cls:
        return jsonify(error="class not found"), 404
    
    # FIX: Check if class is full
    booked_count = conn.execute("SELECT COUNT(*) FROM bookings WHERE class_id = ?", (class_id,)).fetchone()[0]
    if booked_count >= cls["capacity"]:
        return jsonify(error="class is full"), 400
        
    # FIX: Prevent double booking
    already_booked = conn.execute("SELECT id FROM bookings WHERE member_id = ? AND class_id = ?", (session["member_id"], class_id)).fetchone()
    if already_booked:
        return jsonify(error="already booked"), 400

    conn.execute("INSERT INTO bookings (member_id, class_id) VALUES (?, ?)", (session["member_id"], class_id))
    conn.commit()
    return jsonify(status="booked"), 201


@app.get("/api/my/bookings")
@login_required
def my_bookings():
    rows = db().execute("SELECT b.id, c.name, c.starts_at FROM bookings b JOIN classes c ON c.id = b.class_id "
                        "WHERE b.member_id = ?", (session["member_id"],)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/payments/webhook")
def payment_webhook():
    """Called by the payment provider when a member pays their membership."""
    signature = request.headers.get("X-PulsePay-Signature")
    if not signature:
        return jsonify(error="missing signature"), 401
    
    # FIX: Verify HMAC signature
    secret = os.environ.get("PULSEPAY_SECRET", "").encode()
    expected_sig = hmac.new(secret, request.get_data(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_sig, signature):
        return jsonify(error="invalid signature"), 401
        
    # EDGE CASE FIX: Handle invalid JSON gracefully
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Invalid JSON format"), 400

    if body.get("status") == "paid":
        db().execute("UPDATE members SET membership_paid = 1 WHERE id = ?", (body["member_id"],))
        db().commit()
    return jsonify(received=True)


@app.get("/api/admin/members")
@admin_required
def admin_members():
    rows = db().execute("SELECT id, name, email, plan, role, membership_paid FROM members").fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
