from flask import Flask, request, jsonify
from db import db
from flask_cors import CORS
import uuid
import time

app = Flask(__name__)
CORS(app)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'pong'})

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    username = data.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400
    try:
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", username, "hack")
        row = db.execute("SELECT id FROM users WHERE username = ?", username)
        return jsonify({'user_id': row[0]['id'], 'username': username})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Helper: get user_id from request or default to demo
def get_user_id():
    data = request.get_json(silent=True) or {}
    uid = data.get('user_id')
    if uid is None:
        # Fall back to query param?
        uid = request.args.get('user_id', type=int)
    return uid or DEMO_USER_ID

# Example: get current user profile
@app.route('/me', methods=['GET'])
def me():
    user_id = request.args.get('user_id', type=int) or DEMO_USER_ID
    rows = db.execute("SELECT id, username, xp, elo, level FROM users WHERE id = ?", user_id)
    if not rows:
        return jsonify({'error': 'user not found'}), 404
    return jsonify({'user': rows[0]})

# GET exercises
@app.route('/exercises', methods=['GET'])
def get_exercises():
    rows = db.execute("SELECT * FROM exercises")
    return jsonify({'exercises': rows})

# Start a workout session; returns a random session_id string
@app.route('/start_session', methods=['POST'])
def start_session():
    data = request.get_json() or {}
    user_id = get_user_id()
    exercise_id = data.get('exercise_id')
    if not exercise_id:
        return jsonify({'error': 'exercise_id required'}), 400
    # Generate a session_id, e.g., UUID or timestamp-based
    session_id = str(uuid.uuid4())
    # Insert into workout_sessions; minimal fields
    db.execute("""
        INSERT INTO workout_sessions (session_id, user_id, score, start_time, submitted, hidden)
        VALUES (?, ?, ?, datetime('now'), 0, 0)
    """, session_id, user_id, 0)
    return jsonify({'session_id': session_id})

# Submit metrics: accepts a list of metrics for this session and exercise
@app.route('/submit_metrics', methods=['POST'])
def submit_metrics():
    data = request.get_json() or {}
    user_id = get_user_id()
    session_id = data.get('session_id')
    metrics = data.get('metrics')  # Expect list of { exercise_id, type, value }
    if not session_id or not isinstance(metrics, list):
        return jsonify({'error': 'session_id and metrics list required'}), 400
    for m in metrics:
        exercise_id = m.get('exercise_id')
        metric_type = m.get('type')
        metric_value = m.get('value')
        if not (exercise_id and metric_type and metric_value is not None):
            continue  # skip invalid entries
        # Insert into workout_metrics
        db.execute("""
            INSERT INTO workout_metrics (session_id, user_id, exercise_id, metric_type, metric_value, recorded_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, session_id, user_id, exercise_id, metric_type, metric_value)
    return jsonify({'status': 'metrics recorded'})

# End session: finalize performance, update XP/ELO, personal bests
@app.route('/end_session', methods=['POST'])
def end_session():
    data = request.get_json() or {}
    user_id = get_user_id()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'session_id required'}), 400

    # Mark session as submitted
    db.execute("""
        UPDATE workout_sessions SET finish_time = datetime('now'), submitted = 1 WHERE session_id = ? AND user_id = ?
    """, session_id, user_id)

    # Example aggregation: compute total reps or longest hold from workout_metrics
    # Adjust this logic per exercise type; here we just sum a metric named 'reps'
    total_reps = 0
    rows = db.execute("""
        SELECT SUM(metric_value) AS sum_reps FROM workout_metrics
        WHERE session_id = ? AND user_id = ? AND metric_type = 'reps'
    """, session_id, user_id)
    if rows and rows[0]['sum_reps'] is not None:
        total_reps = rows[0]['sum_reps']

    # Compute XP gain: e.g., 1 XP per rep
    xp_gain = int(total_reps)
    # Update user XP
    db.execute("UPDATE users SET xp = xp + ? WHERE id = ?", xp_gain, user_id)
    # Optionally update level if thresholds defined (you can skip if not seeded)
    # Example: retrieve next threshold, compare, etc.

    # Update personal best if applicable (simplified: skip for hackathon or implement basic check)
    # Return a summary
    summary = {
        'total_reps': total_reps,
        'xp_gain': xp_gain
    }
    return jsonify({'summary': summary})

# Leaderboard: show top users by xp or a game_type
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    # For simplicity: order by xp descending, limit top 10
    rows = db.execute("SELECT id, username, xp FROM users ORDER BY xp DESC LIMIT 10")
    return jsonify({'leaderboard': rows})

# AI feedback endpoint: returns a dummy response or real Gemini call
@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json() or {}
    user_id = get_user_id()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'error': 'session_id required'}), 400

    # Fetch metrics from workout_metrics
    metrics = db.execute("""
        SELECT exercise_id, metric_type, metric_value, recorded_at
        FROM workout_metrics WHERE session_id = ? AND user_id = ?
    """, session_id, user_id)
    # Build prompt string summarizing metrics
    prompt_lines = ["You are a virtual coach. User session metrics:"]
    for m in metrics:
        prompt_lines.append(f"- Exercise {m['exercise_id']}: {m['metric_type']} = {m['metric_value']}")
    prompt_lines.append("Provide form tips and progression suggestions.")
    prompt = "\n".join(prompt_lines)

    # Call Gemini API (pseudo-code; implement in utils)
    try:
        from utils import call_gemini_feedback
        feedback_text = call_gemini_feedback(prompt)
    except Exception as e:
        # For hackathon, you may return a dummy response if API not working
        feedback_text = "Great job! Keep going and try to improve form by aligning your body. (Dummy feedback)"
    # Save to ai_feedback_logs
    db.execute("""
        INSERT INTO ai_feedback_logs (session_id, user_id, feedback_text, feedback_data, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, session_id, user_id, feedback_text, str(metrics))

    return jsonify({'feedback': feedback_text})

if __name__ == '__main__':
    # Optionally ensure DB tables exist: you can call your create_db.py logic here
    app.run(host='0.0.0.0', port=5000, debug=True)
