import json
import random
import string
from db import db

# Common first and last names for more realistic usernames
FIRST_NAMES = [
    "alex", "sam", "jordan", "taylor", "morgan",
    "casey", "jamie", "riley", "dakota", "reese",
    "cameron", "devon", "drew", "kai", "skyler",
    "peyton", "blake", "rowan", "quinn", "avery"
]

LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones",
    "miller", "davis", "garcia", "rodriguez", "wilson",
    "martinez", "anderson", "taylor", "thomas", "hernandez",
    "moore", "martin", "jackson", "thompson", "white"
]


def seed_many_users(n=100):
    """Seed approximately n dummy users with realistic usernames, random XP and ELO."""
    created = 0
    tried = set()

    while created < n:
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        base  = f"{first}.{last}"                # e.g. "alex.smith"
        username = base

        # If that base is already taken (or we've already tried), append digits
        suffix = 1
        while username in tried or db.execute("SELECT 1 FROM users WHERE username = ?", username):
            username = f"{base}{suffix}"
            suffix += 1

        tried.add(username)
        email = f"{username}@example.com"

        xp  = random.randint(0, 5000)
        elo = random.randint(800, 1200)
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        try:
            db.execute(
                "INSERT INTO users (username, password, email, xp, elo) VALUES (?, ?, ?, ?, ?)",
                username, password, email, xp, elo
            )
            created += 1
        except Exception as e:
            # if insert fails for any reason, skip and continue
            print(f"Failed to insert {username}: {e}")
            continue

def seed_training_hub_data():
    users = db.execute("SELECT id FROM users")
    if not users:
        print("No users found to seed data for.")
        return

    for user in users:
        user_id = user['id']
        
        # Seed plank times
        for _ in range(random.randint(1, 25)):
            duration = random.randint(20, 300)  # 30 seconds to 5 minutes
            db.execute("INSERT INTO plank_times (user_id, duration_seconds) VALUES (?, ?)", user_id, duration)

        # Seed vsit times
        for _ in range(random.randint(1, 25)):
            duration = random.randint(20, 300)  # 30 seconds to 5 minutes
            db.execute("INSERT INTO vsit_times (user_id, duration_seconds) VALUES (?, ?)", user_id, duration)

        # Seed pushup reps
        for _ in range(random.randint(1, 25)):
            reps = random.randint(5, 50)  # 5 to 50 pushups
            db.execute("INSERT INTO pushup_reps (user_id, reps) VALUES (?, ?)", user_id, reps)

def main():
    pass


if __name__ == "__main__":
    main()
