import json
import random
import string
from db import db
from tqdm import tqdm
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

CLUBS = [
    "Fitness Fanatics", "Health Warriors", "Active Achievers",
    "Elite Performance Center", "Strength & Conditioning Institute", 
    "Precision Fitness Academy", "Summit Athletics Club",
    "Optimal Health Solutions", "Premier Wellness Collective",
    "Everest Performance Labs", "Velocity Training Systems",
    "CoreFit Professional", "Pinnacle Athletic Club",
    "Revolution Fitness Studio", "Elevate Health & Performance",
    "Dynamic Fitness Professionals", "Apex Training Center",
    "Momentum Health Group", "Ascend Wellness Institute",
    "Catalyst Athletics Club", "Integrated Fitness Solutions"
]

def seed_many_users(n=100):
    """Seed approximately n dummy users with realistic usernames, random XP and ELO."""
    created = 0
    tried = set()

    with tqdm(total=n, desc="Seeding users") as progress_bar:
        while created < n:
            first = random.choice(FIRST_NAMES)
            last  = random.choice(LAST_NAMES)
            base  = f"{first}.{last}"
            username = base

            suffix = 1
            while username in tried or db.execute("SELECT 1 FROM users WHERE username = ?", username):
                username = f"{base}{suffix}"
                suffix += 1

            tried.add(username)
            email = f"{username}@example.com"

            xp  = random.randint(0, 5000)
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            try:
                db.execute(
                    "INSERT INTO users (username, password, email, xp) VALUES (?, ?, ?, ?)",
                    username, password, email, xp
                )
                created += 1
                progress_bar.update(1)
            except Exception as e:
                print(f"Failed to insert {username}: {e}")
                continue
            
            # random club
            club_id = random.randint(1, len(CLUBS))
            db.execute(
                "INSERT INTO club_members (club_id, user_id) VALUES (?, ?)",
                club_id, db.execute("SELECT id FROM users WHERE username = ?", username)[0]['id']
            )
    
def seed_clubs():
    for club in CLUBS:
        db.execute("INSERT INTO clubs (name) VALUES (?)", club)

def seed_training_hub_data():
    id = db.execute("SELECT id FROM users WHERE username = 'admin'")[0]['id']
    for i in range(30):
        db.execute("INSERT INTO plank_times (user_id, duration) VALUES (?, ?)", id, random.randint(200, 300))
        db.execute("INSERT INTO vsit_times (user_id, duration) VALUES (?, ?)", id, random.randint(200, 300))
        db.execute("INSERT INTO pushup_reps (user_id, reps) VALUES (?, ?)", id, random.randint(30, 50))

def seed_me():
    db.execute("INSERT INTO users (username, password, email, xp) VALUES (?, ?, ?, ?)",
               "admin", "admin", "admin@example.com", 5000)
    db.execute("INSERT INTO club_members (club_id, user_id) VALUES (?, ?)",
               1, 101)


def main():
    seed_clubs()
    seed_many_users(100)  # Adjust the number of users as needed
    seed_training_hub_data()
    seed_me()


if __name__ == "__main__":
    main()
