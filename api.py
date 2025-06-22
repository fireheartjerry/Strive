from flask import Flask, request, jsonify, g
from flask_cors import CORS
from db import db
import uuid
from functools import wraps

app = Flask(__name__)

# ─── CORS CONFIG ─────────────────────────────────────────────────────────────
CORS(app,
    supports_credentials=True,
    origins=["http://localhost:3000", "https://project-qijqqts4mdd64pxnl85a.framercanvas.com", "https://strivespurhacks.framer.website"],
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"]
)

# ─── HELPER: AUTH DECORATOR ──────────────────────────────────────────────────
def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # 1) Let CORS preflight through
        if request.method == "OPTIONS":
            return jsonify({}), 200

        # 2) Now enforce your Bearer token
        auth_header = request.headers.get("Authorization", "")
        token       = auth_header.replace("Bearer ", "", 1)
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        user = db.execute(
          "SELECT * FROM users WHERE session_token = ?", token
        )
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401

        g.user = user[0]
        return f(*args, **kwargs)
    return wrapper

# ─── AUTH ROUTES ─────────────────────────────────────────────────────────────
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



# ─── PROTECTED ROUTES ────────────────────────────────────────────────────────
@app.route('/me', methods=['GET'])
@auth_required
def me():
    row = db.execute(
        "SELECT id, username, email, xp FROM users WHERE id = ?",
        g.user['id']
    )
    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(row[0])

@app.route('/getplankdata', methods=['GET'])
@auth_required
def get_plank_data():
    row = db.execute(
        "SELECT duration FROM plank_times WHERE user_id = ? ORDER BY duration ASC LIMIT 1",
        g.user['id']
    )
    if not row:
        return jsonify({'error': 'No plank data found.'}), 404
    return jsonify(row[0])

@app.route('/getvsitdata', methods=['GET'])
@auth_required
def get_vsit_data():
    row = db.execute(
        "SELECT duration FROM vsit_times WHERE user_id = ? ORDER BY duration ASC LIMIT 1",
        g.user['id']
    )
    if not row:
        return jsonify({'error': 'No vsit data found.'}), 404
    return jsonify(row[0])

@app.route('/getpushupdata', methods=['GET'])
@auth_required
def get_pushup_data():
    row = db.execute(
        "SELECT reps FROM pushups_reps WHERE user_id = ? ORDER BY reps DESC LIMIT 1",
        g.user['id']
    )
    if not row:
        return jsonify({'error': 'No pushup data found.'}), 404
    return jsonify(row[0])

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
        'leaderboard': rows,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
