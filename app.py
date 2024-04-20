from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import timedelta
from dotenv import load_dotenv
import json
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('TOKEN')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
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


def load_credentials():
    with open('credentials.json', 'r') as file:
        credentials = json.load(file)
    return credentials['username'], credentials['password']


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        stored_username, stored_password = load_credentials()
        if username == stored_username and password == stored_password:
            user = User(1)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=1)
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    load_logs()
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    criteria = request.form
    results = []
    for log in logs:
        if all(item in log.items() for item in criteria.items()):
            results.append(log)
    return jsonify(results)


@app.route('/filters', methods=['GET'])
def get_filters():
    command_names = set(log['command_name'] for log in logs)
    user_names = set(log['user_name'] for log in logs)
    return jsonify({'command_names': list(command_names), 'user_names': list(user_names)})


if __name__ == '__main__':
    app.run(debug=True)
