from flask import render_template, redirect, url_for, request, flash, session
from flask_wtf.csrf import validate_csrf, CSRFError
from sqlalchemy.exc import SQLAlchemyError
from app.models.db import get_db_connection, User
from app.utils.random_username import generate_random_usernames
from sqlalchemy import text
import bleach

def choose_username():
    """Display username choices and handle the selection."""
    
    # Check if a user is logged in or if there's a pending user
    user = session.get('user')
    pending_user = session.get('pending_user')
    
    if not user and not pending_user:
        flash("Please log in to choose a username.", "error")
        return redirect(url_for('auth.login'))
    
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
            
            # Update session
            if pending_user:
                session['user'] = {'id': user_id, 'name': username, 'email': email}
                session.pop('pending_user', None)
            else:
                session['user']['name'] = username
            
            session.modified = True
            flash("Username successfully set!", "success")
            return redirect(url_for('view.index'))
        
        # Handle database errors
        except SQLAlchemyError as e:
            print(f"Database Error: {e}")
            session_db.rollback()
            return "Database error", 500

    # GET request handling
    if pending_user:
        usernames = pending_user.get('usernames')
        email = pending_user.get('email')
    else:
        usernames = generate_random_usernames()
        email = user['email']
        session['pending_user'] = {'email': email, 'usernames': usernames}
        session.modified = True

    return render_template('profile/choose_username.html', usernames=usernames, email=email)

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