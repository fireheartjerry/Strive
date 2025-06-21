from db import db
import random
from datetime import datetime, timedelta
import hashlib

# Configuration for dummy data
NUM_USERS = 20
NUM_EXERCISES = 10
NUM_WORKOUTS_PER_USER = 5
NUM_CONTESTS = 3

def random_datetime(start_days_ago=365):
    base = datetime.now() - timedelta(days=start_days_ago)
    return (base + timedelta(days=random.randint(0, start_days_ago))).strftime('%Y-%m-%d %H:%M:%S')

def hash_password(password):
    # simple SHA256 hash for dummy passwords
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == '__main__':
    # Populate trainers
    trainers = [
        ('Alice', 'http://example.com/voice/alice.mp3', 'Expert yoga instructor'),
        ('Bob', 'http://example.com/voice/bob.mp3', 'Strength coach'),
        ('Charlie', 'http://example.com/voice/charlie.mp3', 'Cardio specialist')
    ]
    trainer_ids = []
    for name, url, bio in trainers:
        trainer_ids.append(db.execute(
            "INSERT INTO trainers (name, voice_url, bio) VALUES (?, ?, ?)",
            name, url, bio
        ))

    # Populate users
    user_ids = []
    for i in range(1, NUM_USERS + 1):
        username = f'user{i}'
        password = hash_password('password')
        email = f'user{i}@example.com'
        join_date = random_datetime()
        twofa = random.choice([0, 1])
        workouts_completed = random.randint(0, 20)
        events_completed = random.randint(0, 10)
        rating = random.randint(800, 2400)
        user_ids.append(db.execute(
            "INSERT INTO users (username, password, email, join_date, twofa, workouts_completed, events_completed, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            username, password, email, join_date, twofa, workouts_completed, events_completed, rating
        ))

    # Populate exercises
    # Base exercises list
    exercises = [
        ('Push-up', 'Standard push-up exercise', 'chest, triceps', 'easy', ''),
        ('Squat', 'Bodyweight squat', 'legs, glutes', 'medium', ''),
        ('Plank', 'Core stability hold', 'core', 'easy', ''),
        ('Burpee', 'Full-body cardio', 'full body', 'hard', ''),
        ('Lunge', 'Alternating lunges', 'legs', 'medium', '')
    ]
    # Add generic exercises to reach NUM_EXERCISES
    for i in range(len(exercises)+1, NUM_EXERCISES+1):
        exercises.append((
            f'Exercise {i}',
            f'Description for exercise {i}',
            random.choice(['arms', 'legs', 'core', 'full body']),
            random.choice(['easy', 'medium', 'hard']),
            ''
        ))
    exercise_ids = []
    for name, desc, muscles, diff, media in exercises:
        exercise_ids.append(db.execute(
            "INSERT INTO exercises (name, description, muscle_groups, difficulty, media_url) VALUES (?, ?, ?, ?, ?)",
            name, desc, muscles, diff, media
        ))

    # Populate workouts and workout_exercises
    workout_ids = []
    for uid in user_ids:
        for _ in range(NUM_WORKOUTS_PER_USER):
            duration = random.randint(10, 60)
            mode = random.choice(['strength', 'cardio', 'mixed'])
            trainer = random.choice(trainer_ids)
            feedback = 'Good session'
            wid = db.execute(
                "INSERT INTO workouts (user_id, duration, mode, trainer_id, feedback) VALUES (?, ?, ?, ?, ?)",
                uid, duration, mode, trainer, feedback
            )
            workout_ids.append(wid)
            # link exercises
            for eid in random.sample(exercise_ids, 3):
                db.execute(
                    "INSERT INTO workout_exercises (workout_id, exercise_id, reps, sets, time_held, rating, notes, result_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    wid, eid, random.randint(5, 15), random.randint(1, 5), random.randint(10, 60), random.randint(1, 5), '', ''
                )

    # Populate user-trainers (each user assigned a random trainer)
    for uid in user_ids:
        db.execute(
            "INSERT INTO user_trainers (user_id, trainer_id) VALUES (?, ?)",
            uid, random.choice(trainer_ids)
        )

    # Populate leaderboard
    for idx, uid in enumerate(sorted(user_ids, key=lambda x: random.random()), 1):
        db.execute(
            "INSERT INTO leaderboard (user_id, category, score, rank) VALUES (?, ?, ?, ?)",
            uid, 'global', random.randint(0, 1000), idx
        )

    # Populate contests and entries
    contest_ids = []
    for ci in range(1, NUM_CONTESTS + 1):
        name = f'Contest {ci}'
        cid = db.execute(
            "INSERT INTO contests (name, description, mode, host_user_id, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)",
            name, f'{name} description', 'timed', random.choice(user_ids), random_datetime(30), random_datetime(1)
        )
        contest_ids.append(cid)
        for uid in random.sample(user_ids, 3):
            db.execute(
                "INSERT INTO contest_entries (contest_id, user_id, score) VALUES (?, ?, ?)",
                cid, uid, random.randint(0, 500)
            )

    # Populate groups and members
    group_ids = []
    for title in ['Team A', 'Team B']:
        gid = db.execute(
            "INSERT INTO groups (name, description, created_by) VALUES (?, ?, ?)",
            title, f'{title} description', random.choice(user_ids)
        )
        group_ids.append(gid)
        # members
        members = random.sample(user_ids, 3)
        for m in members:
            db.execute(
                "INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, ?)",
                gid, m, 1 if m == members[0] else 0
            )

    # Populate achievements and user_achievements
    ach_ids = []
    for aname in ['First Login', '100 Workouts', 'Marathon Runner']:
        aid = db.execute(
            "INSERT INTO achievements (name, description, icon) VALUES (?, ?, ?)",
            aname, f'Achievement for {aname}', ''
        )
        ach_ids.append(aid)
        # unlock for random user
        db.execute(
            "INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)",
            random.choice(user_ids), aid
        )

    # Populate workout_heatmap
    for uid in user_ids:
        for d in range(30):
            date = (datetime.now() - timedelta(days=d)).strftime('%Y-%m-%d')
            db.execute(
                "INSERT INTO workout_heatmap (user_id, date, workout_count) VALUES (?, ?, ?)",
                uid, date, random.randint(0, 2)
            )

    # Populate invites for each group
    for gid in group_ids:
        for _ in range(2):
            email = f'invite{random.randint(100,999)}@example.com'
            status = random.choice(['pending', 'accepted', 'declined'])
            db.execute(
                "INSERT INTO invites (group_id, invited_user_email, status) VALUES (?, ?, ?)",
                gid, email, status
            )
    print('Database populated with extended dummy data.')
