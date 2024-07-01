from flask import render_template, redirect, url_for, request, flash, session
from sqlalchemy.exc import SQLAlchemyError
from flask_wtf.csrf import validate_csrf, CSRFError
from app.models.db import get_db_connection, User
from app.utils.streaks import update_login_streak
from sqlalchemy import text
import bleach

def login():
    # Validate the CSRF token
    if request.method == 'POST':      
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash("Invalid CSRF token", "error")
            return render_template('auth/login.html')
        
        # Sanitize email and password
        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        
        # Validate email and password
        if not email or not password:
            flash('Email and password are required', "error")
            return redirect(url_for('auth.login'))
        try:
            with get_db_connection() as session_db:
                result = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email})
                user = result.fetchone()
            
            # Check if the user exists
            if not user:
                flash('User does not exist. Please register.', "error")
                return redirect(url_for('auth.login'))
            
            # Convert the user tuple to a dictionary
            user_dict = user._mapping
            
            # Check if the user has verified their email
            if not user_dict['email_verified']:
                flash('Please verify your email address before logging in.', 'error')
                session['unverified_user'] = user_dict['email']
                return render_template('auth/login.html', unverified=True)
            
            # Query the user object from the database
            user_obj = session_db.query(User).filter_by(id=user_dict['id']).first()
            
            # Check the password and redirect to choose_username if the user has not set a name
            if user_obj.check_password(password):
                session['user'] = {'id': user_obj.id, 'name': user_obj.name, 'email': user_obj.email, 'is_admin': user_obj.is_admin}
                session.modified = True
                if user_obj.name is None:
                    return redirect(url_for('auth.choose_username'))
                else:
                    update_login_streak(user_obj, session_db)
                return redirect(url_for('view.index'))
            else:
                flash('Invalid email or password', "error")
                return redirect(url_for('auth.login'))
        
        # Handle database errors
        except SQLAlchemyError as e:
            flash(f"An error occurred while processing your request: {e}", "error")
            return render_template('auth/login.html')
    return render_template('auth/login.html')

def logout():
    """
    Log out the current user by clearing the session.
    """
    session.pop('user', None)
    session.clear()
    response = redirect(url_for('view.index'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response