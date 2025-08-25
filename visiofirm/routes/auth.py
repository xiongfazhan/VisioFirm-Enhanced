from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from visiofirm.models.user import create_user, get_user_by_username, get_user_by_email, update_user, User
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        user_data = get_user_by_username(identifier) or get_user_by_email(identifier)
        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6])
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password', 'error')
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        company = request.form['company']
        if not all([first_name, last_name, username, email, password]):
            flash('All required fields must be filled', 'error')
        elif create_user(first_name, last_name, username, email, password, company):
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Username or email already exists', 'error')
    return render_template('register.html')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        company = request.form.get('company')

        updates = {}
        if first_name:
            updates['first_name'] = first_name
        if last_name:
            updates['last_name'] = last_name
        if email:
            updates['email'] = email
        if password:
            updates['password_hash'] = generate_password_hash(password)
        if company:
            updates['company'] = company

        if not updates:
            flash('No changes provided', 'error')
            return redirect(url_for('auth.profile'))

        success = update_user(current_user.id, updates)
        if success:
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Email already exists', 'error')

    return render_template('profile.html', user=current_user)

@bp.route('/profile_data', methods=['GET'])
@login_required
def profile_data():
    try:
        avatar = f"{current_user.first_name[0]}.{current_user.last_name[0]}" if current_user.first_name and current_user.last_name else ""
        return jsonify({'success': True, 'avatar': avatar})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        if not password:
            flash('Password cannot be empty', 'error')
            return render_template('reset.html')
        if password != password_confirm:
            flash('Passwords do not match', 'error')
            return render_template('reset.html')
        user_data = get_user_by_username(identifier) or get_user_by_email(identifier)
        if user_data:
            password_hash = generate_password_hash(password)
            success = update_user(user_data[0], {'password_hash': password_hash})
            if success:
                flash('Password reset successful. Please log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Error resetting password', 'error')
        else:
            flash('Invalid username or email', 'error')
    return render_template('reset.html')