import sqlite3

db = sqlite3.connect("unit_inspector.db")
db.execute("PRAGMA foreign_keys = ON")

# ── Login table ──────────────────────────────────────────
db.executescript("""
CREATE TABLE IF NOT EXISTS Login (
    user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT UNIQUE NOT NULL,
    password  TEXT NOT NULL,      -- hash in production
    user_type TEXT NOT NULL       -- 'admin' or 'user'
);
INSERT OR IGNORE INTO Login (user_id, username, password, user_type) VALUES
    (1,'admin','123456','admin'),
    (2,'demo','demo123','user');
""")

# ── Schedule table (one row per user) ────────────────────
db.executescript("""
CREATE TABLE IF NOT EXISTS Schedule (
    sched_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER NOT NULL,
    courses  TEXT DEFAULT '[]',   -- JSON list
    days     TEXT DEFAULT '[]',   -- JSON list
    time     TEXT DEFAULT '08:00',
    UNIQUE(user_id),
    FOREIGN KEY (user_id) REFERENCES Login(user_id)
);
""")

# ensure every user has a blank schedule row
db.executemany(
    "INSERT OR IGNORE INTO Schedule (user_id) VALUES (?)",
    [(row[0],) for row in db.execute("SELECT user_id FROM Login")]
)

db.commit()
db.close()
print("unit_inspector.db created and initialised.")
