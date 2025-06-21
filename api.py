from flask import Flask, request, jsonify
from db import *

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
