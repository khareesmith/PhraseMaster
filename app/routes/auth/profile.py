from flask import render_template, redirect, url_for, request, flash, session
from flask_wtf.csrf import validate_csrf, CSRFError
from sqlalchemy.exc import SQLAlchemyError
from app.models.db import get_db_connection, User
from app.utils.random_username import generate_random_usernames
from sqlalchemy import text
import bleach

def choose_username():
    """Display username choices and handle the selection."""
    
    # Check if a user is logged in
    user = session.get('user')
    pending_user = session.get('pending_user')
    
    if request.method == 'POST':
        # Validate the CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash("Invalid CSRF token", "error")
            return redirect(url_for('auth.login'))

        # Validate and sanitize username
        username = bleach.clean(request.form['username'])
        
        if pending_user:
            email = pending_user.get('email')
        elif user:
            email = user.get('email')
        else:
            return redirect(url_for('auth.login'))

        session_db = get_db_connection()
        try:
            with session_db.no_autoflush:
                user_record = session_db.query(User).filter_by(email=email).one()
                
                # Find User ID and Username
                if user_record:
                    user_id = user_record.id
                    user_record.name = username
                    
                    # Update submissions with the new username
                    session_db.execute(text("UPDATE submissions SET username = :new_username WHERE user_id = :user_id"), {'new_username': username, 'user_id': user_id})
                
            session_db.commit()
            
            # Sets the session user dictionary with the user's name and email
            session['pending_user']['username'] = username
            session['user'] = {'id': user_id, 'name': user_record.name, 'email': email}
            session.pop('pending_user', None)
            session.modified = True
            return redirect(url_for('view.index'))
        
        # Handle database errors
        except SQLAlchemyError as e:
            print(f"Database Error: {e}")
            session_db.rollback()
            return "Database error", 500

    if not pending_user and not user:
        return redirect(url_for('auth.login'))

    if pending_user:
        usernames = pending_user['usernames']
    else:
        usernames = generate_random_usernames()
        session['pending_user'] = {'email': user['email'], 'usernames': usernames}
        session.modified = True

    is_first_time = 'name' not in session['user'] or session['user']['name'] is None
    return render_template('profile/choose_username.html', usernames=usernames, is_first_time=is_first_time)

def change_password():
    """Allow users to change their password."""
    user_session = session.get('user')
    
    # Redirect to the login page if the user is not logged in
    if not user_session:
        return redirect(url_for('auth.login'))
    
    session_db = get_db_connection()
    try:
        result = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': user_session['email']}).fetchone()
        
        if result:
            user_record = result._mapping
        else:
            user_record = None
        
        # Check if the user is a Google user
        if not user_record or user_record['google_user']:
            flash('You cannot change your password here. Please use Google to manage your account.', 'error')
            return redirect(url_for('view.profile'))
        
        if request.method == 'POST':
            # Validate the CSRF token
            try:
                validate_csrf(request.form.get('csrf_token'))
            except CSRFError:
                flash("Invalid CSRF token", "error")
                return redirect(url_for('auth.login'))
            
            # Sanitize the form inputs
            current_password = bleach.clean(request.form['current_password'])
            new_password = bleach.clean(request.form['new_password'])
            confirm_password = bleach.clean(request.form['confirm_password'])
            
            # Check if the new password and confirm password match
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return redirect(url_for('auth.change_password'))
            
            # Check if the new password is the same as the current password
            if current_password == new_password:
                flash('New password must be different from the current password', 'error')
                return redirect(url_for('auth.change_password'))
            
            # Check if the current password is correct
            user = User(**user_record)
            if not user.check_password(current_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('auth.change_password'))
            
            # Create a new password hash and update the user's password
            user.set_password(new_password)
            session_db.execute(
                text('UPDATE users SET password_hash = :password_hash, password_salt = :password_salt WHERE email = :email'),
                {'password_hash': user.password_hash, 'password_salt': user.password_salt, 'email': user_session['email']}
            )
            session_db.commit()
            
            flash('Password updated successfully', 'success')
            return redirect(url_for('view.profile'))
        
    # Handle database errors
    except SQLAlchemyError as e:
        print(f"Database Error: {e}")
        session_db.rollback()
        flash('An error occurred while updating your password. Please try again.', 'error')
        return redirect(url_for('auth.change_password'))
    finally:
        session_db.close()
    
    return render_template('profile/change_password.html')

def generate_usernames():
    """Generate new random usernames and update the session."""
    pending_user = session.get('pending_user')
    
    if not pending_user:
        return redirect(url_for('auth.login'))
    
    # Generate 3 new random usernames and update the pending_user for the session
    random_usernames = generate_random_usernames()
    session['pending_user']['usernames'] = random_usernames
    session.modified = True
    return redirect(url_for('auth.choose_username'))