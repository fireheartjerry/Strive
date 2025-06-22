from db import *

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(64) NOT NULL,
    email VARCHAR(128) UNIQUE,
    join_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    xp INTEGER DEFAULT 0,
    date_of_birth DATE,
    gender TEXT,
    height_cm REAL,
    weight_kg REAL
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS plank_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS vsit_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS pushup_reps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reps INTEGER NOT NULL,
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(256) NOT NULL,
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS club_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    UNIQUE(club_id, user_id)
);
""")
