from flask import Blueprint, request, session, redirect, jsonify, render_template
from werkzeug.security import check_password_hash
from database.connection import DatabaseConnection
from utils.decorators import api_response

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', error=None)
        
    username = request.form.get('username')
    password = request.form.get('password')
    
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT id, username, password_hash, role, full_name FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        
        # Role-based redirect
        if user['role'] == 'admin':
            return redirect('/admin')
        elif user['role'] == 'teacher':
            return redirect('/dashboard')
        else:
            return redirect('/portal')
            
    return render_template('login.html', error="Invalid username or password")

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@auth_bp.route('/api/me')
@api_response
def me():
    if 'user_id' not in session:
        return {"error": "Not logged in"}, 401
    return {
        "id": session['user_id'],
        "username": session['username'],
        "role": session['role'],
        "full_name": session['full_name']
    }
