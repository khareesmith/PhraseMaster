from flask import Blueprint, redirect, url_for, session, current_app, render_template, request
from flask_wtf.csrf import validate_csrf
from authlib.integrations.flask_client import OAuthError
from ..models.db import get_db_connection, create_user
from ..utils.random_username import generate_random_username, generate_random_usernames
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login/<provider>')
def login(provider):
    """
    Initiate the OAuth login process for the specified provider.
    """
    oauth_provider = current_app.extensions['authlib.integrations.flask_client'].create_client(provider)
    redirect_uri = url_for('auth.authorize', provider=provider, _external=True)
    return oauth_provider.authorize_redirect(redirect_uri, scope='openid email profile')

@auth_bp.route('/authorize/<provider>')
def authorize(provider):
    """
    Handle the callback from the OAuth provider and log in or create the user.
    """
    session['oauth_provider'] = provider  # Store the provider in the session
    try:
        oauth_provider = current_app.extensions['authlib.integrations.flask_client'].create_client(provider)
        token = oauth_provider.authorize_access_token()
        user_info = oauth_provider.userinfo()
    except OAuthError as error:
        print(f"OAuth Error: {error}")  # Log the error for debugging
        return "Authorization failed", 500
    
    # Implement user creation or retrieval logic
    session_db = get_db_connection()
    try:
        user = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': user_info['email']}).fetchone()
        
        if not user:
            random_usernames = generate_random_usernames()
            session['pending_user'] = {'email': user_info['email'], 'usernames': random_usernames}
            return redirect(url_for('auth.choose_username'))
    
        if user:
            session['user'] = {'id': user.id, 'name': user.name}
            session_db.commit()
            return redirect(url_for('view.index'))
        else:
            session_db.rollback()
            return "User creation or retrieval failed", 500

    except SQLAlchemyError as e:
        session_db.rollback()
        print(f"SQLAlchemy Error: {e}")
        return "Database error", 500
    finally:
        session_db.close()

@auth_bp.route('/choose_username', methods=['GET', 'POST'])
def choose_username():
    """Display username choices and handle the selection."""
    if request.method == 'POST':

        validate_csrf(request.form.get('csrf_token'))
        
        chosen_username = request.form.get('username')
        pending_user = session.get('pending_user')

        if not pending_user or not chosen_username:
            return redirect(url_for('auth.login'))

        session_db = get_db_connection()
        try:
            create_user(session_db, pending_user['email'], chosen_username)
            user = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': pending_user['email']}).fetchone()
            
            if user:
                session['user'] = {'id': user.id, 'name': user.name}
                session_db.commit()
                return redirect(url_for('view.index'))
            else:
                session_db.rollback()
                return "User creation failed", 500
        except SQLAlchemyError as e:
            print(f"Database Error: {e}")  # Log the error for debugging
            session_db.rollback()
            return "Database error", 500

    pending_user = session.get('pending_user')
    if not pending_user:
        return redirect(url_for('auth.login'))

    print("Current Usernames in Session: ", pending_user['usernames'])  # Debugging line
    return render_template('choose_username.html', usernames=pending_user['usernames'])

@auth_bp.route('/generate_usernames')
def generate_usernames():
    """Generate new random usernames and update the session."""
    pending_user = session.get('pending_user')
    
    if not pending_user:
        return redirect(url_for('auth.login'))
    
    random_usernames = generate_random_usernames()
    print("Generated Usernames: ", random_usernames)  # Debugging line
    session['pending_user']['usernames'] = random_usernames
    session.modified = True  # Mark the session as modified to ensure changes are saved
    print(session['pending_user']['usernames'])
    print("Session updated with new usernames")  # Debugging line
    return redirect(url_for('auth.choose_username'))


@auth_bp.route('/logout')
def logout():
    """
    Log out the current user by clearing the session.
    """
    session.pop('user', None)
    session.clear()  # Ensure all session data is cleared
    response = redirect(url_for('view.index'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response