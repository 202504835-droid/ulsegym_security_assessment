"""Creates a fresh database with test data. Run automatically when the container starts."""
import os
import sqlite3
from werkzeug.security import generate_password_hash  # FIX: Imported secure hashing

DB_PATH = os.environ.get("DB_PATH", "/data/pulsegym.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
c = sqlite3.connect(DB_PATH)
c.executescript("""
CREATE TABLE members (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT, phone TEXT,
                      plan TEXT, role TEXT DEFAULT 'member', membership_paid INTEGER DEFAULT 0, notes TEXT);
CREATE TABLE classes (id INTEGER PRIMARY KEY, name TEXT, coach TEXT, starts_at TEXT, capacity INTEGER);
CREATE TABLE bookings (id INTEGER PRIMARY KEY, member_id INTEGER, class_id INTEGER);
""")
# FIX: Use generate_password_hash instead of MD5
hash_pw = lambda p: generate_password_hash(p) 

members = [
    ("Sara Adel", "sara@pulsegym.test", "sara12345", "0100 000 0001", "annual", "member", 1, "Prefers morning classes"),
    ("Omar Hany", "omar@pulsegym.test", "omar12345", "0100 000 0002", "monthly", "member", 0, "Payment overdue, call before Dec 1"),
    ("Mona Fathy", "mona@pulsegym.test", "mona12345", "0100 000 0003", "quarterly", "member", 1, "Recovering from knee injury"),
    ("Desk Admin", "admin@pulsegym.test", "Adm1n!PulseGym#2026", "0100 000 0099", "staff", "admin", 1, ""),
]
c.executemany("INSERT INTO members (name, email, password_hash, phone, plan, role, membership_paid, notes) "
              "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [(n, e, hash_pw(p), ph, pl, r, paid, no) for n, e, p, ph, pl, r, paid, no in members])
c.executemany("INSERT INTO classes (name, coach, starts_at, capacity) VALUES (?, ?, ?, ?)", [
    ("Morning Yoga", "Hala", "2026-12-05T07:00:00Z", 20), ("Spin", "Karim", "2026-12-05T18:00:00Z", 15),
    ("HIIT", "Youssef", "2026-12-06T19:00:00Z", 12), ("Pilates", "Nour", "2026-12-07T10:00:00Z", 10)])
c.commit()
print("Seeded", DB_PATH)
