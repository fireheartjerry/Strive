import json
import random
from db import db

# populate_db.py: Seed initial data for GymForces hackathon
# Assumes create_db.py has been run and tables exist.

def seed_demo_user():
    rows = db.execute("SELECT id FROM users WHERE username = ?", "demo")
    if rows:
        return rows[0]['id']
    else:
        db.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", "demo", "hack", "demo@example.com")
        rows = db.execute("SELECT id FROM users WHERE username = ?", "demo")
        return rows[0]['id']


def seed_many_users(n=100):
    """Seed approximately n dummy users with random XP and ELO."""
    for i in range(1, n+1):
        username = f"user{i:03d}"
        email = f"{username}@example.com"
        # Check if user exists
        rows = db.execute("SELECT id FROM users WHERE username = ?", username)
        if rows:
            continue
        # Random XP between 0 and 5000, random elo around 1000±200
        xp = random.randint(0, 5000)
        elo = random.randint(800, 1200)
        # Insert user with dummy password
        try:
            db.execute("INSERT INTO users (username, password, email, xp, elo) VALUES (?, ?, ?, ?, ?)",
                       username, "hack", email, xp, elo)
        except Exception:
            pass


def seed_muscle_groups():
    muscle_groups = [
        ("Core", "Muscles of the core, including abdominals and lower back."),
        ("Chest", "Pectoral muscles."),
        ("Back", "Latissimus dorsi, rhomboids, and other back muscles."),
        ("Legs", "Quadriceps, hamstrings, calves."),
        ("Arms", "Biceps, triceps, forearms."),
        ("Shoulders", "Deltoids and related muscles."),
        ("Glutes", "Gluteal muscles."),
        ("Full Body", "Exercises targeting multiple muscle groups.")
    ]
    for name, desc in muscle_groups:
        try:
            db.execute("INSERT INTO muscle_groups (name, description) VALUES (?, ?)", name, desc)
        except Exception:
            pass


def seed_exercises(demo_user_id):
    exercises = [
        {
            "id": "plank",
            "name": "Plank",
            "description": "Hold a plank position with a straight body.",
            "difficulty": "beginner",
            "equipment_required": "none",
            "media_url": "",
            "created_by": demo_user_id
        },
        {
            "id": "pushups",
            "name": "Push-ups",
            "description": "Standard push-ups with proper form.",
            "difficulty": "beginner",
            "equipment_required": "none",
            "media_url": "",
            "created_by": demo_user_id
        },
        {
            "id": "squats",
            "name": "Bodyweight Squats",
            "description": "Standard bodyweight squats focusing on depth and form.",
            "difficulty": "beginner",
            "equipment_required": "none",
            "media_url": "",
            "created_by": demo_user_id
        },
        {
            "id": "lunges",
            "name": "Lunges",
            "description": "Forward lunges alternating legs.",
            "difficulty": "beginner",
            "equipment_required": "none",
            "media_url": "",
            "created_by": demo_user_id
        },
        {
            "id": "burpees",
            "name": "Burpees",
            "description": "Full-body exercise combining squat, plank, and jump.",
            "difficulty": "intermediate",
            "equipment_required": "none",
            "media_url": "",
            "created_by": demo_user_id
        }
    ]
    for ex in exercises:
        try:
            db.execute(
                """
                INSERT INTO exercises (id, name, description, difficulty, equipment_required, media_url, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ex["id"], ex["name"], ex["description"], ex["difficulty"], ex["equipment_required"], ex["media_url"], ex["created_by"])
        except Exception:
            pass
    
    mapping = {
        "plank": ["Core", "Full Body"],
        "pushups": ["Chest", "Arms", "Shoulders"],
        "squats": ["Legs", "Glutes"],
        "lunges": ["Legs", "Glutes"],
        "burpees": ["Full Body", "Legs", "Arms", "Core"]
    }
    for ex_id, mg_names in mapping.items():
        for mg_name in mg_names:
            rows = db.execute("SELECT id FROM muscle_groups WHERE name = ?", mg_name)
            if rows:
                mg_id = rows[0]["id"]
                try:
                    db.execute("INSERT INTO exercise_muscle_groups (exercise_id, muscle_group_id) VALUES (?, ?)", ex_id, mg_id)
                except Exception:
                    pass


def seed_trainers():
    trainers = [
        {
            "name": "Alice Trainer",
            "bio": "Certified calisthenics coach with 5 years of experience.",
            "certifications": "CPT,Calisthenics Instructor",
            "experience_years": 5,
            "specialization": "calisthenics",
            "profile_pic": "",
            "contact_info": "alice@example.com"
        },
        {
            "name": "Bob Coach",
            "bio": "Fitness enthusiast specializing in full-body workouts.",
            "certifications": "Fitness Nutrition, Strength Training",
            "experience_years": 3,
            "specialization": "full body",
            "profile_pic": "",
            "contact_info": "bob@example.com"
        }
    ]
    for tr in trainers:
        try:
            db.execute(
                """
                INSERT INTO trainers (name, bio, certifications, experience_years, specialization, profile_pic, contact_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, tr["name"], tr["bio"], tr["certifications"], tr["experience_years"], tr["specialization"], tr["profile_pic"], tr["contact_info"])
        except Exception:
            pass


def seed_trainer_availability():
    trainers = db.execute("SELECT id FROM trainers")
    for row in trainers:
        trainer_id = row["id"]
        for day in range(1, 6):  # Monday=1 .. Friday=5
            try:
                db.execute(
                    "INSERT INTO trainer_availability (trainer_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
                    trainer_id, day, "08:00", "17:00")
            except Exception:
                pass


def seed_user_trainers(demo_user_id):
    trainers = db.execute("SELECT id FROM trainers ORDER BY id")
    if trainers:
        trainer_id = trainers[0]["id"]
        try:
            db.execute("INSERT INTO user_trainers (user_id, trainer_id) VALUES (?, ?)", demo_user_id, trainer_id)
        except Exception:
            pass


def seed_level_thresholds():
    thresholds = [
        (1, 0),
        (2, 100),
        (3, 250),
        (4, 500),
        (5, 1000),
        (6, 2000),
        (7, 3500),
        (8, 5500),
        (9, 8000),
        (10, 11000)
    ]
    for level, xp_req in thresholds:
        try:
            db.execute("INSERT INTO level_thresholds (level, xp_required) VALUES (?, ?)", level, xp_req)
        except Exception:
            pass


def seed_achievements():
    achievements = [
        {"name": "First Workout", "description": "Complete your first workout session.", "icon": "", "xp_reward": 10},
        {"name": "Ten Workouts", "description": "Complete 10 workout sessions.", "icon": "", "xp_reward": 50},
        {"name": "First Plank", "description": "Complete your first plank session.", "icon": "", "xp_reward": 5},
        {"name": "First Pushups", "description": "Complete your first pushup session.", "icon": "", "xp_reward": 5},
        {"name": "Marathon Reps", "description": "Accumulate 1000 total reps across sessions.", "icon": "", "xp_reward": 100}
    ]
    for ach in achievements:
        try:
            db.execute(
                "INSERT INTO achievements (name, description, icon, xp_reward) VALUES (?, ?, ?, ?)", ach["name"], ach["description"], ach["icon"], ach["xp_reward"])
        except Exception:
            pass


def seed_notifications(demo_user_id):
    try:
        content = "Welcome to GymForces! Start your first workout to earn XP and achievements."
        db.execute("INSERT INTO notifications (user_id, type, content) VALUES (?, ?, ?)",
                   demo_user_id, "welcome", content)
    except Exception:
        pass


def seed_user_settings(demo_user_id):
    settings = {"theme": "dark", "notifications": True}
    try:
        db.execute("INSERT INTO user_settings (user_id, settings_json) VALUES (?, ?)" , demo_user_id, json.dumps(settings))
    except Exception:
        pass


def seed_workout_list(demo_user_id):
    try:
        db.execute("INSERT INTO workout_list (owner_user_id, name, description) VALUES (?, ?, ?)",
                   demo_user_id, "My Routine", "Demo workout routine with basic exercises.")
        row = db.execute("SELECT id FROM workout_list WHERE owner_user_id = ? AND name = ?", demo_user_id, "My Routine")
        list_id = row[0]["id"]
        exercises = ["plank", "pushups", "squats"]
        order = 1
        for ex in exercises:
            try:
                db.execute("INSERT INTO workout_in_list (workout_list_id, exercise_id, order_index) VALUES (?, ?, ?)",
                           list_id, ex, order)
                order += 1
            except Exception:
                pass
    except Exception:
        pass


def main():
    # Seed demo user
    demo_user_id = seed_demo_user()
    # Seed many dummy users
    seed_many_users(100)
    # Other seeds
    seed_muscle_groups()
    seed_exercises(demo_user_id)
    seed_trainers()
    seed_trainer_availability()
    seed_user_trainers(demo_user_id)
    seed_level_thresholds()
    seed_achievements()
    seed_notifications(demo_user_id)
    seed_user_settings(demo_user_id)
    seed_workout_list(demo_user_id)
    print("Database population complete.")

if __name__ == "__main__":
    main()
