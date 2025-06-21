from db import *

# USERS: extended profile for GymForces
db.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(64) NOT NULL,
    email VARCHAR(128) UNIQUE,
    join_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    xp INTEGER DEFAULT 0,
    elo INTEGER DEFAULT 1000,
    level INTEGER DEFAULT 1,
    bio TEXT,
    profile_pic TEXT,
    date_of_birth DATE,
    gender TEXT,
    height_cm REAL,
    weight_kg REAL
);
""")

# ANNOUNCEMENTS: general updates/notifications
db.execute("""
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(256) NOT NULL,
    content TEXT,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""")

# FRIENDSHIPS: social features
db.execute("""
CREATE TABLE IF NOT EXISTS friendships (
    user_id INTEGER NOT NULL,
    friend_user_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'accepted', 'blocked'
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at DATETIME,
    PRIMARY KEY (user_id, friend_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (friend_user_id) REFERENCES users(id)
);
""")

# MUSCLE GROUPS
db.execute("""
CREATE TABLE IF NOT EXISTS muscle_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) NOT NULL UNIQUE,
    description TEXT
);
""")

# EXERCISES: metadata about exercises
db.execute("""
CREATE TABLE IF NOT EXISTS exercises (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    difficulty VARCHAR(32),          -- e.g., 'beginner', 'intermediate', 'advanced'
    equipment_required TEXT,         -- e.g., 'none', 'pull-up bar'
    media_url TEXT,                  -- link to image/video demonstration
    created_by INTEGER,              -- user or admin who added
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
""")

# LINK EXERCISES TO MUSCLE GROUPS (many-to-many)
db.execute("""
CREATE TABLE IF NOT EXISTS exercise_muscle_groups (
    exercise_id VARCHAR(64) NOT NULL,
    muscle_group_id INTEGER NOT NULL,
    PRIMARY KEY (exercise_id, muscle_group_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (muscle_group_id) REFERENCES muscle_groups(id)
);
""")

# TRAINER PROFILES
db.execute("""
CREATE TABLE IF NOT EXISTS trainers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(128) NOT NULL,
    bio TEXT,
    certifications TEXT,           -- comma-separated or JSON text
    experience_years INTEGER,
    specialization TEXT,           -- e.g., 'calisthenics', 'yoga', ...
    rating REAL DEFAULT 0,         -- average rating from users
    rating_count INTEGER DEFAULT 0,
    profile_pic TEXT,
    contact_info TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""")

# USER-TRAINER ASSIGNMENTS (personal trainer matches)
db.execute("""
CREATE TABLE IF NOT EXISTS user_trainers (
    user_id INTEGER NOT NULL,
    trainer_id INTEGER NOT NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'completed', 'cancelled'
    PRIMARY KEY (user_id, trainer_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (trainer_id) REFERENCES trainers(id)
);
""")

# TRAINER AVAILABILITY (optional scheduling)
db.execute("""
CREATE TABLE IF NOT EXISTS trainer_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,   -- 0=Sunday .. 6=Saturday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id)
);
""")

# TRAINER REVIEWS
db.execute("""
CREATE TABLE IF NOT EXISTS trainer_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# WORKOUT SESSIONS: repurposed from TopsOJ workout_sessions
db.execute("""
CREATE TABLE IF NOT EXISTS workout_sessions (
    session_id VARCHAR(32) NOT NULL,
    user_id INTEGER NOT NULL,
    score REAL NOT NULL DEFAULT 0,        -- could reflect performance metrics
    start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finish_time DATETIME,
    hidden INTEGER NOT NULL DEFAULT 0,
    submitted BOOLEAN NOT NULL DEFAULT 0,
    elo_change INTEGER,
    admin BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (session_id, user_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# COMPLETED EXERCISES WITHIN A SESSION
db.execute("""
CREATE TABLE IF NOT EXISTS completed_exercises (
    session_id VARCHAR(32) NOT NULL,
    user_id INTEGER NOT NULL,
    exercise_id VARCHAR(64) NOT NULL,
    reps INTEGER,
    sets INTEGER,
    time_held INTEGER,                   -- seconds
    calories_burned REAL,
    notes TEXT,
    completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, user_id, exercise_id),
    FOREIGN KEY (session_id, user_id) REFERENCES workout_sessions(session_id, user_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
""")

# SESSION EXERCISE METADATA (like scoring rules)
db.execute("""
CREATE TABLE IF NOT EXISTS session_exercises (
    session_id VARCHAR(32) NOT NULL,
    exercise_id VARCHAR(64) NOT NULL,
    name VARCHAR(256) NOT NULL,
    point_value INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(64),
    form_check TEXT NOT NULL,            -- e.g., criteria or JSON schema
    draft BOOLEAN NOT NULL DEFAULT 0,
    reps_min INTEGER NOT NULL DEFAULT 0,
    reps_max INTEGER NOT NULL DEFAULT 0,
    target_users INTEGER NOT NULL DEFAULT -1,
    form_hint VARCHAR(256) NOT NULL DEFAULT '',
    requires_equipment BOOLEAN NOT NULL DEFAULT 0,
    submission_limit INTEGER NOT NULL DEFAULT -1,
    media_reference TEXT,
    PRIMARY KEY (session_id, exercise_id)
);
""")

# EXERCISE DEPENDENCIES (prerequisite relationships)
db.execute("""
CREATE TABLE IF NOT EXISTS exercise_dependencies (
    session_id VARCHAR(32) NOT NULL,
    exercise_id VARCHAR(64) NOT NULL,
    required_id VARCHAR(64) NOT NULL,
    PRIMARY KEY (session_id, required_id, exercise_id),
    FOREIGN KEY (session_id, exercise_id) REFERENCES session_exercises(session_id, exercise_id),
    FOREIGN KEY (required_id) REFERENCES exercises(id)
);
""")

# RATE LIMIT (for API calls or feature usage)
db.execute("""
CREATE TABLE IF NOT EXISTS rate_limit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    limit_id TEXT NOT NULL DEFAULT 'exercise_feedback',
    user_id INTEGER NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# GAME LEADERBOARD (e.g., longest plank, most pushups)
db.execute("""
CREATE TABLE IF NOT EXISTS game_leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_type VARCHAR(64) NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    achieved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# GAME TIMES (last attempt times)
db.execute("""
CREATE TABLE IF NOT EXISTS game_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_type VARCHAR(64) NOT NULL,
    last_play_time DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# RATING UPDATES (history of ELO or rating changes)
db.execute("""
CREATE TABLE IF NOT EXISTS rating_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(32) NOT NULL,
    old_rating INTEGER,
    new_rating INTEGER,
    change INTEGER,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# TRAINING COURSES (structured programs or challenges)
db.execute("""
CREATE TABLE IF NOT EXISTS training_courses (
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    description TEXT,
    difficulty VARCHAR(32),
    duration_weeks INTEGER,
    created_by INTEGER,
    date_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    public BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
""")

# EXERCISE ATTEMPTS (in-progress attempts)
db.execute("""
CREATE TABLE IF NOT EXISTS exercise_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id VARCHAR(64) NOT NULL,
    user_id INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status TEXT NOT NULL DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'abandoned'
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# EXERCISE TODO LIST
db.execute("""
CREATE TABLE IF NOT EXISTS exercise_todo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exercise_id VARCHAR(64) NOT NULL,
    priority INTEGER DEFAULT 0,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
""")

# WORKOUT LISTS (custom plans)
db.execute("""
CREATE TABLE IF NOT EXISTS workout_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL,
    name VARCHAR(256),
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS workout_in_list (
    workout_list_id INTEGER NOT NULL,
    exercise_id VARCHAR(64) NOT NULL,
    order_index INTEGER DEFAULT 0,
    PRIMARY KEY (workout_list_id, exercise_id),
    FOREIGN KEY (workout_list_id) REFERENCES workout_list(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
""")

# FITNESS TOURNAMENTS (competitions among users/groups)
db.execute("""
CREATE TABLE IF NOT EXISTS tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(256),
    description TEXT,
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(32),  -- e.g., 'upcoming', 'ongoing', 'completed'
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS tournament_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(128),
    tournament_id INTEGER NOT NULL,
    created_by INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS tournament_team_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES tournament_teams(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS tournament_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    session_id VARCHAR(32) NOT NULL,
    user_id INTEGER NOT NULL,
    score_multiplier REAL NOT NULL DEFAULT 1.0,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
    FOREIGN KEY (session_id, user_id) REFERENCES workout_sessions(session_id, user_id)
);
""")

# API KEYS
db.execute("""
CREATE TABLE IF NOT EXISTS api_keys (
    apikey VARCHAR(256) NOT NULL,
    user_id INTEGER,
    apikeycreationdate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    platform VARCHAR(256) NOT NULL,
    PRIMARY KEY (apikey),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# ACHIEVEMENTS & USER ACHIEVEMENTS
db.execute("""
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(128) NOT NULL UNIQUE,
    description TEXT,
    icon TEXT,
    xp_reward INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""")

db.execute("""
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    unlocked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (achievement_id) REFERENCES achievements(id),
    UNIQUE(user_id, achievement_id)
);
""")

# WORKOUT HEATMAP (daily summary)
db.execute("""
CREATE TABLE IF NOT EXISTS workout_heatmap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    workout_count INTEGER DEFAULT 0,
    total_time INTEGER DEFAULT 0,    -- total seconds
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date)
);
""")

# PERSONAL BESTS
db.execute("""
CREATE TABLE IF NOT EXISTS personal_bests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exercise_id VARCHAR(64) NOT NULL,
    best_value REAL NOT NULL,
    best_date DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    UNIQUE(user_id, exercise_id)
);
""")

# WORKOUT METRICS LOGS: raw data per exercise attempt
db.execute("""
CREATE TABLE IF NOT EXISTS workout_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(32) NOT NULL,
    user_id INTEGER NOT NULL,
    exercise_id VARCHAR(64) NOT NULL,
    metric_type VARCHAR(64) NOT NULL,  -- e.g., 'angle_deviation', 'speed', 'heart_rate'
    metric_value REAL NOT NULL,
    recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id, user_id) REFERENCES workout_sessions(session_id, user_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
""")

# AI FEEDBACK LOGS
db.execute("""
CREATE TABLE IF NOT EXISTS ai_feedback_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(32) NOT NULL,
    user_id INTEGER NOT NULL,
    feedback_text TEXT,
    feedback_data TEXT,   -- JSON blob with detailed metrics or suggestions
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id, user_id) REFERENCES workout_sessions(session_id, user_id)
);
""")

# XP LOGS: track XP changes
db.execute("""
CREATE TABLE IF NOT EXISTS xp_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    xp_change INTEGER NOT NULL,
    reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# LEVEL THRESHOLDS: define XP required per level
db.execute("""
CREATE TABLE IF NOT EXISTS level_thresholds (
    level INTEGER PRIMARY KEY,
    xp_required INTEGER NOT NULL
);
""")

# NOTIFICATIONS
db.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type VARCHAR(64),
    content TEXT,
    is_read BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# USER SETTINGS / PREFERENCES
db.execute("""
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    settings_json TEXT,  -- JSON blob for preferences: theme, notifications, etc.
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# DEVICE REGISTRATION (for push notifications)
db.execute("""
CREATE TABLE IF NOT EXISTS user_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_token VARCHAR(256) NOT NULL,
    device_type VARCHAR(64),  -- e.g., 'ios', 'android', 'web'
    registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# TRAINING PLAN SUBSCRIPTIONS: users subscribing to courses
db.execute("""
CREATE TABLE IF NOT EXISTS user_training_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_id VARCHAR(64) NOT NULL,
    subscribed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    progress_json TEXT,    -- JSON tracking progress through the course
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES training_courses(id),
    UNIQUE(user_id, course_id)
);
""")

# LOGS: system logs for auditing if needed
db.execute("""
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,        -- nullable for system-wide logs
    action VARCHAR(128),
    details TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")
