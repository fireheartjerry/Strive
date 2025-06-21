import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# USERS
cursor.execute("""
CREATE TABLE 'users' (
    'id' integer PRIMARY KEY NOT NULL,
    'username' varchar(20) NOT NULL UNIQUE,
    'password' varchar(64) NOT NULL,
    'email' varchar(128) UNIQUE,
    'join_date' datetime NOT NULL DEFAULT(0),
    'twofa' boolean NOT NULL DEFAULT(0),
    'workouts_completed' integer NOT NULL DEFAULT(0),
    'events_completed' integer NOT NULL DEFAULT(0),
    'rating' integer,
);
""")

# EXERCISES
cursor.execute("""
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    muscle_groups TEXT,
    difficulty TEXT,
    media_url TEXT
);
""")

# WORKOUTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    duration INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode TEXT,
    trainer_id INTEGER,
    feedback TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (trainer_id) REFERENCES trainers(id)
);
""")

# WORKOUT EXERCISES
cursor.execute("""
CREATE TABLE IF NOT EXISTS workout_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    reps INTEGER,
    sets INTEGER,
    time_held INTEGER,
    rating INTEGER,
    notes TEXT,
    result_data TEXT,
    FOREIGN KEY (workout_id) REFERENCES workouts(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
""")

# LEADERBOARD
cursor.execute("""
CREATE TABLE IF NOT EXISTS leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    score INTEGER NOT NULL,
    rank INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# CONTESTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS contests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    mode TEXT,
    host_user_id INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    FOREIGN KEY (host_user_id) REFERENCES users(id)
);
""")

# CONTEST ENTRIES
cursor.execute("""
CREATE TABLE IF NOT EXISTS contest_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    score INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contest_id) REFERENCES contests(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# GROUPS
cursor.execute("""
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
""")

# GROUP MEMBERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# INVITES
cursor.execute("""
CREATE TABLE IF NOT EXISTS invites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    invited_user_email TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups(id)
);
""")

# TRAINERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS trainers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    voice_url TEXT,
    bio TEXT
);
""")

# USER TRAINERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_trainers (
    user_id INTEGER NOT NULL,
    trainer_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (trainer_id) REFERENCES trainers(id),
    PRIMARY KEY (user_id)
);
""")

# USER ACHIEVEMENTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (achievement_id) REFERENCES achievements(id)
);
""")

# WORKOUT HEATMAP
cursor.execute("""
CREATE TABLE IF NOT EXISTS workout_heatmap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    workout_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

conn.commit()
conn.close()
