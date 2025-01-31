from flask import Flask, request, session, redirect, url_for, render_template, jsonify
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def select(self, table, columns, where=None, params=()):
        query = f"SELECT {columns} FROM {table}"
        if where:
            query += f" WHERE {where}"
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.close()
        return result

    def insert(self, table, columns, values):
        placeholders = ', '.join(['?'] * len(values))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        conn.close()

    def update(self, table, set_clause, where, params):
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    def delete(self, table, where, params):
        query = f"DELETE FROM {table} WHERE {where}"
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()

db = Database('app.db')

USERS = {
    "admin": "password123",
    "user1": "pass1"
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    db.select("users", "*")

@app.route('/')
@login_required
def index():
    return f"Привіт, {session['user']}! Ви залогінені."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.select('users', '*', 'username = ? AND password = ?', (username, password))
        if user:
            session['user'] = username
            return redirect(url_for('index'))
        return "Неправильне ім'я користувача або пароль", 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/protected')
@login_required
def protected():
    return f"Це захищений контент для користувача {session['user']}."

@app.route('/users', methods=['GET'])
def get_users():
    users = db.select('users', '*')
    return jsonify(users)

@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    existing_user = db.select('users', 'id', 'username = ?', (username,))
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    db.insert('users', 'username, password', (username, password))
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/items', methods=['GET'])
def get_items():
    items = db.select('items', '*')
    return jsonify(items)

@app.route('/items', methods=['POST'])
def add_item():
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    db.insert('items', 'name, description', (name, description))
    return jsonify({'message': 'Item added successfully'}), 201

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
