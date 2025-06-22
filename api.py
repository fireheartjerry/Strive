from flask import Flask, request, jsonify
from flask_cors import CORS
from db import db
import uuid
from gemini_helper import generate_workout_plan

app = Flask(__name__)

ADMIN_ID = 101

CORS(app,
    supports_credentials=True,
    origins=["http://localhost:3000", "https://project-qijqqts4mdd64pxnl85a.framercanvas.com", "https://strivespurhacks.framer.website"],
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"]
)

@app.route('/create_user', methods=['POST'])
def create_user():
    data     = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    email    = data.get('email', '').lower()

    if not username or not password or not email:
        return jsonify({'error': 'Ensure all fields are filled.'}), 400

    try:
        db.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            username, password, email
        )
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    data     = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Ensure all fields are filled.'}), 400

    row = db.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        username, password
    )
    if not row:
        return jsonify({'error': 'Invalid credentials'}), 401

    token = str(uuid.uuid4())
    db.execute("UPDATE users SET session_token = ? WHERE id = ?", token, row[0]['id'])
    print("→ issued token", token, "for user_id", row[0]["id"])

    return jsonify({'user_id': row[0]['id'], 'token': token, 'username': username})


@app.route('/me', methods=['GET'])
def me():
    row = db.execute(
        "SELECT id, username, email, xp FROM users WHERE id = ?",
        ADMIN_ID
    )
    
    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(row[0])

@app.route('/getplankdata', methods=['GET'])
def get_plank_data():
    row = db.execute(
        "SELECT duration FROM plank_times WHERE user_id = ? ORDER BY duration ASC LIMIT 1",
        ADMIN_ID
    )
    if not row:
        return jsonify({'error': 'No plank data found.'}), 404
    return jsonify(row[0])

@app.route('/getvsitdata', methods=['GET'])
def get_vsit_data():
    row = db.execute(
        "SELECT duration FROM vsit_times WHERE user_id = ? ORDER BY duration ASC LIMIT 1",
        ADMIN_ID
    )
    if not row:
        return jsonify({'error': 'No vsit data found.'}), 404
    return jsonify(row[0])

@app.route('/getpushupdata', methods=['GET'])
def get_pushup_data():
    row = db.execute(
        "SELECT reps FROM pushup_reps WHERE user_id = ? ORDER BY reps DESC LIMIT 1",
        ADMIN_ID
    )
    if not row:
        return jsonify({'error': 'No pushup data found.'}), 404
    return jsonify(row[0])

@app.route('/my_club', methods=['GET'])
def my_club():
    club = db.execute(
        "SELECT c.id, c.name FROM clubs c JOIN club_members cm ON c.id = cm.club_id WHERE cm.user_id = ?",
        ADMIN_ID
    )
    
    if not club:
        return jsonify({'error': 'No club found for this user'}), 404
    
    return jsonify(club[0])

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    offset   = (page - 1) * per_page

    rows = db.execute(
        "SELECT id, username, xp FROM users ORDER BY xp DESC LIMIT ? OFFSET ?",
        per_page, offset
    )
    total = db.execute("SELECT COUNT(*) as count FROM users")[0]['count']
    total_pages = (total + per_page - 1) // per_page

    return jsonify({
        'lb': rows,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }
    })

@app.route("/club_leaderboards", methods=['GET'])
def get_club_members():
    club_id = db.execute("SELECT club_id FROM club_members WHERE user_id = ?", ADMIN_ID)[0]['club_id']
    
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    offset   = (page - 1) * per_page

    rows = db.execute(
        "SELECT u.id, u.username, u.xp FROM club_members cm JOIN users u ON cm.user_id = u.id WHERE cm.club_id = ? ORDER BY u.xp DESC LIMIT ? OFFSET ?",
        club_id, per_page, offset
    )
    
    total = db.execute("SELECT COUNT(*) as count FROM club_members WHERE club_id = ?", club_id)[0]['count']
    total_pages = (total + per_page - 1) // per_page
    
    if not rows:
        return jsonify({'error': 'No members found for this club'}), 404
    
    return jsonify({
        'lb': rows,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }
    })
    
@app.route('/clubs', methods=['GET'])
def get_clubs():
    """
    Returns a list of all clubs.
    """
    rows = db.execute("SELECT name FROM clubs")
    return jsonify(clubs=rows)

@app.route('/generate_plan', methods=['GET'])
def generate_plan():
    """
    Protected endpoint that takes a JSON payload:
      { "type": "plank" | "vsit" | "pushup" }
    and returns:
      { "plan": "<generated workout plan text>" }
    """
    workout_type = request.args.get('type')
    if workout_type not in ('plank', 'vsit', 'pushup'):
        return jsonify(error="Invalid or missing workout type"), 400

    # Fetch raw history and compute average
    if workout_type in ("plank", "vsit"):
        rows = db.execute(
            f"SELECT duration FROM {workout_type}_times WHERE user_id = ? ORDER BY duration ASC",
            ADMIN_ID
        )
        history = [r['duration'] for r in rows]
    else:  # pushup
        rows = db.execute(
            "SELECT reps FROM pushup_reps WHERE user_id = ? ORDER BY reps DESC",
            ADMIN_ID
        )
        history = [r['reps'] for r in rows]

    average = (sum(history) / len(history)) if history else 0.0

    try:
        plan = generate_workout_plan(workout_type, history, average)
    except GeminiAPIError as e:
        return jsonify(error=str(e)), 500

    return jsonify(plan=plan)
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
