from flask import render_template, redirect, url_for, request, flash
from flask_wtf.csrf import validate_csrf, CSRFError
from app.models.db import get_db_connection, User
from app.utils.email import send_pass_reset_email, is_valid_email
from app.utils.token import generate_confirmation_token, confirm_token
from app.utils.auth import is_strong_password
from sqlalchemy import text
import bleach

def reset_password_request():
    if request.method == 'POST':
        # Validate the CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash("Invalid CSRF token", "error")
            return redirect(url_for('auth.login'))

        # Sanitize the email
        email = bleach.clean(request.form['email'])
        
        # Check if the email is valid
        if not is_valid_email(email):
            flash('Invalid email address.', 'error')
            return render_template('auth/reset_password_request.html')
        
        with get_db_connection() as session_db:
            user = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email}).fetchone()
            
            # Check if the user exists and send a password reset email
            if user:
                token = generate_confirmation_token(email)
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                html = render_template('auth/reset_password_email.html', reset_url=reset_url)
                send_pass_reset_email([email], html)
                flash('A password reset email has been sent. Please check your Inbox and Spam folder.', 'success')
            else:
                flash('Email not found.', 'error')
                return redirect(url_for('auth.reset_password_request'))
                
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_req.html')

def reset_password(token):
    try:
        email = confirm_token(token)
    except Exception as e:
        print(f"Token confirmation error: {e}")
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.reset_password_request'))
    
    if request.method == 'POST':
        # Validate the CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError as e:
            flash("Invalid CSRF token", "error")
            return redirect(url_for('auth.reset_password', token=token))
        
        # Sanitize the password and confirm password
        password = bleach.clean(request.form['password'])
        confirm_password = bleach.clean(request.form['confirm_password'])
        
        # Check if the passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.reset_password', token=token))
        
        # Validate the password strength
        password_result = is_strong_password(password)
        if password_result['score'] < 3:
            suggestions = " ".join(password_result['feedback']['suggestions'])
            flash(f"Password is too weak. Suggestions: {suggestions}", 'error')
            return redirect(url_for('auth.reset_password', token=token))
        
        with get_db_connection() as session_db:
            result = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email}).fetchone()
            
            if result:
                user_record = result._mapping
                user = User(**user_record)
                user.set_password(password)
                
                session_db.execute(
                    text('UPDATE users SET password_hash = :password_hash, password_salt = :password_salt WHERE email = :email'),
                    {'password_hash': user.password_hash, 'password_salt': user.password_salt, 'email': email}
                )
                session_db.commit()
                flash('Your password has been reset successfully.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('User not found.', 'error')
                return redirect(url_for('auth.reset_password_request'))
    
    return render_template('auth/reset_password.html', token=token)