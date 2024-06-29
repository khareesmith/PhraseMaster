from flask import render_template, redirect, url_for, request, flash, session
from sqlalchemy.exc import SQLAlchemyError
from flask_wtf.csrf import validate_csrf, CSRFError
from app.models.db import get_db_connection, User
from app.utils.email import send_verification_email, is_valid_email
from app.utils.token import generate_confirmation_token, confirm_token
from app.utils.auth import is_strong_password
from sqlalchemy import text
import bleach

def register():
    # Validate the CSRF token
    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash("Invalid CSRF token", "error")
            return render_template('auth/register.html')
        
        # Validate and sanitize email and password
        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        
        # Validate email and password
        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template('auth/register.html')
        
        # Validate email format
        if not is_valid_email(email):
            flash("Invalid email format.", "error")
            return render_template('auth/register.html')
        
        # Validate password strength
        password_result = is_strong_password(password)
        if password_result['score'] < 3:
            suggestions = " ".join(password_result['feedback']['suggestions'])
            flash(f"Password is too weak. Suggestions: {suggestions}", "error")
            return render_template('auth/register.html')
        
        try:
            with get_db_connection() as session_db:
                # Check if the email is already registered
                existing_user = session_db.execute(
                    text('SELECT * FROM users WHERE email = :email'), {'email': email}
                ).fetchone()
                if existing_user:
                    flash("Email is already registered.", "error")
                    return render_template('auth/register.html')
                
                # New user registration
                new_user = User(email=email, email_verified=False)
                new_user.set_password(password)
                session_db.add(new_user)
                session_db.commit()
                
                # Send verification email
                token = generate_confirmation_token(new_user.email)
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                html = render_template('auth/confirm_email.html', confirm_url=confirm_url)
                send_verification_email([new_user.email], html) 
                flash('A verification email has been sent to your email address.', 'success')
                return redirect(url_for('auth.login'))
        
        # Handle database errors
        except SQLAlchemyError as e:
            print(f"Database Error: {e}")
            session_db.rollback()
            flash("An error occurred during registration. Please try again.", "error")
            return render_template('auth/register.html')
        
    return render_template('auth/register.html')

def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('auth.login'))
    
    with get_db_connection() as session_db:
        user = session_db.execute(
            text('SELECT * FROM users WHERE email = :email'), {'email': email}
        ).fetchone()
        
        # Check if the user exists
        if user is None:
            flash('Account not found.', 'error')
            return redirect(url_for('auth.register'))

        # Check if the user is already verified and update the email_verified status if not
        if user.email_verified:
            flash('Account already confirmed. Please login.', 'success')
        else:
            session_db.execute(
                text('UPDATE users SET email_verified = :email_verified WHERE email = :email'), 
                {'email_verified': True, 'email': email}
            )
            session_db.commit()
            flash('You have confirmed your account. Thanks!', 'success')
    
    return redirect(url_for('auth.login'))

def resend_verification():
    if request.method == 'POST':
        # Validate the CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash("Invalid CSRF token", "error")
            return redirect(url_for('auth.login'))
        
        # Check if there is an unverified email in the session
        email = session.get('unverified_user')
        if not email:
            flash('No unverified email found.', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            with get_db_connection() as session_db:
                user = session_db.execute(
                    text('SELECT * FROM users WHERE email = :email'), {'email': email}
                ).fetchone()
                
                # Check if the user exists and has not verified their email. Resend the verification email if the user exists
                if user and not user.email_verified:
                    token = generate_confirmation_token(email)
                    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                    html = render_template('auth/confirm_email.html', confirm_url=confirm_url)
                    send_verification_email([email], html)
                    flash(f'A verification email has been sent to {email}. Please check your Inbox and Spam folder.', 'success')
                else:
                    flash('User not found or already verified.', 'error')
        
        # Handle database errors
        except SQLAlchemyError as e:
            session_db.rollback()
            flash(f"An error occurred: {e}", 'error')
            return "Database error", 500
    
    return redirect(url_for('auth.login'))