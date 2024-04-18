from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Load the log file
logs = []
def load_logs():
    global logs
    logs = []
    with open('discord_bot.log', 'r') as file:
        for line in file:
            try:
                log = json.loads(line)
                logs.append(log)
            except json.JSONDecodeError:
                print(f"Error parsing line: {line}")

load_logs()

@app.route('/')
def index():
    load_logs()
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    load_logs()
    criteria = request.form
    results = []
    for log in logs:
        if all(item in log.items() for item in criteria.items()):
            results.append(log)
    return jsonify(results)

@app.route('/filters', methods=['GET'])
def get_filters():
    load_logs()
    command_names = set(log['command_name'] for log in logs)
    user_names = set(log['user_name'] for log in logs)
    return jsonify({'command_names': list(command_names), 'user_names': list(user_names)})

if __name__ == '__main__':
    app.run(debug=True)
