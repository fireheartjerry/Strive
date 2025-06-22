from flask import Flask, request, jsonify, session
from flask_session import Session
from db import db
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

Session(app)

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    email = data.get('email').lower()

    if not username or not password or not email:
        return jsonify({'error': 'Ensure all fields are filled.'}), 400
    try:
        db.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", username, password, email)
        row = db.execute("SELECT id FROM users WHERE username = ?", username)
        return jsonify({'user_id': row[0]['id'], 'username': username})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    session.clear()
    session.permanent = True
    
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Ensure all fields are filled.'}), 400

    row = db.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", username, password)
    if not row:
        return jsonify({'error': 'Invalid credentials.'}), 401

    session['user_id'] = row[0]['id']
    session['username'] = row[0]['username']
    
    return jsonify({'user_id': row[0]['id'], 'username': row[0]['username']})

@app.route('/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated.'}), 401
    
    user_id = session['user_id']
    row = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    
    if not row:
        return jsonify({'error': 'User not found.'}), 404
    
    return jsonify(row[0])

# Leaderboard: show top users by xp or a game_type
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Calculate offset for pagination
    offset = (page - 1) * per_page
    
    # Get paginated results
    rows = db.execute(
        "SELECT id, username, xp FROM users ORDER BY xp DESC LIMIT ? OFFSET ?", 
        per_page, offset
    )
    
    # Get total count for pagination metadata
    total = db.execute("SELECT COUNT(*) as count FROM users")[0]['count']
    total_pages = (total + per_page - 1) // per_page  # ceiling division
    
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
    # Optionally ensure DB tables exist: you can call your create_db.py logic here
    app.run(host='0.0.0.0', port=5000, debug=True)
