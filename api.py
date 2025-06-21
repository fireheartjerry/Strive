from flask import Flask, request, jsonify
from db import db

app = Flask(__name__)

# Register API endpoints without decorators

def ping():
    return jsonify({'message': 'pong'})

app.add_url_rule('/ping', 'ping', ping, methods=['GET'])

# Example POST endpoint

def echo():
    data = request.get_json() or {}
    return jsonify({'you_sent': data})

app.add_url_rule('/echo', 'echo', echo, methods=['POST'])

# New GET endpoint for glebber
@app.route('/glebber', methods=['GET'])
def glebber():
    return jsonify({'message': 'glebber'})

# Rankings endpoint sorted by elo
def rankings():
    rows = db.execute("SELECT id, username, rating AS elo FROM users ORDER BY elo DESC")
    return jsonify({'rankings': rows})

app.add_url_rule('/rankings', 'rankings', rankings, methods=['GET'])

# Additional API endpoints for database tables
def get_users():
    rows = db.execute(
        "SELECT * FROM users ORDER BY rating DESC"
    )
    return jsonify({'users': rows})
app.add_url_rule('/users', 'get_users', get_users, methods=['GET'])

def get_user(user_id):
    rows = db.execute(
        "SELECT * FROM users WHERE id = ?", user_id
    )
    user = rows[0] if rows else {}
    return jsonify({'user': user})
app.add_url_rule('/users/<int:user_id>', 'get_user', get_user, methods=['GET'])

def get_exercises():
    rows = db.execute("SELECT * FROM exercises")
    return jsonify({'exercises': rows})
app.add_url_rule('/exercises', 'get_exercises', get_exercises, methods=['GET'])

def get_workouts():
    rows = db.execute("SELECT * FROM workouts")
    return jsonify({'workouts': rows})
app.add_url_rule('/workouts', 'get_workouts', get_workouts, methods=['GET'])

def get_leaderboard():
    rows = db.execute("SELECT * FROM leaderboard ORDER BY score DESC")
    return jsonify({'leaderboard': rows})
app.add_url_rule('/leaderboard', 'get_leaderboard', get_leaderboard, methods=['GET'])

def get_contests():
    rows = db.execute("SELECT * FROM contests")
    return jsonify({'contests': rows})
app.add_url_rule('/contests', 'get_contests', get_contests, methods=['GET'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
