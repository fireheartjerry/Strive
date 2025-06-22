from flask import Flask, request, jsonify, session
from flask_session import Session
from flask_cors import CORS
from db import db

app = Flask(__name__)

# ─── CONFIG ────────────────────────────────────────────────────────────────
app.config.update({
    'SECRET_KEY':              'replace-with-a-secure-random-value',
    'SESSION_TYPE':            'filesystem',
    'SESSION_PERMANENT':       True,
    'SESSION_COOKIE_SAMESITE': 'Lax',      # allow cross-site
    'SESSION_COOKIE_SECURE':   False,       # set True if using HTTPS in production
    # 'SESSION_COOKIE_DOMAIN':  'localhost', # optional; only if you need domain-specific cookies
})

CORS(
    app,
    resources={r"/*": {
        "origins": [
            "https://project-qijqqts4mdd64pxnl85a.framercanvas.com",
            "http://localhost:3000"
        ]
    }},
    supports_credentials=True
)

Session(app)
# ────────────────────────────────────────────────────────────────────────────

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
        row = db.execute("SELECT id FROM users WHERE username = ?", username)
        return jsonify({'user_id': row[0]['id'], 'username': username}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    session.clear()
    session.permanent = True

    data     = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Ensure all fields are filled.'}), 400

    row = db.execute(
        "SELECT id, username FROM users WHERE username = ? AND password = ?",
        username, password
    )
    if not row:
        return jsonify({'error': 'Invalid credentials.'}), 401

    session['user_id']  = row[0]['id']
    session['username'] = row[0]['username']
    print(session)
    return jsonify({'user_id': row[0]['id'], 'username': row[0]['username']})

@app.route('/me', methods=['GET'])
def me():
    print(session)
    # this will only work if the browser supplies the session cookie
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated.'}), 401

    user_id = session['user_id']
    row = db.execute(
        "SELECT id, username, email, xp FROM users WHERE id = ?",
        user_id
    )
    if not row:
        return jsonify({'error': 'User not found.'}), 404

    return jsonify(row[0])

@app.route('/getplankdata', methods=['GET'])
def get_plank_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated.'}), 401

    row = db.execute(
        "SELECT duration FROM plank_times WHERE user_id = ? ORDER BY duration ASC LIMIT 1",
        user_id
    )
    if not row:
        return jsonify({'error': 'No plank data found.'}), 404

    return jsonify(row)

@app.route('/getvsitdata', methods=['GET'])
def get_vsit_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated.'}), 401

    row = db.execute(
        "SELECT duration FROM vsit_times WHERE user_id = ? ORDER BY duration ASC LIMIT 1",
        user_id
    )
    if not row:
        return jsonify({'error': 'No vsit data found.'}), 404

    return jsonify(row[0])

@app.route('/getpushupdata', methods=['GET'])
def get_pushup_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated.'}), 401

    row = db.execute(
        "SELECT reps FROM pushups_reps WHERE user_id = ? ORDER BY reps DESC LIMIT 1",
        user_id
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
    # Make sure to always hit the same host (localhost:5000)
    app.run(host='0.0.0.0', port=5000, debug=True)
