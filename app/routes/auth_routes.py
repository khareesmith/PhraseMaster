from flask import Blueprint, redirect, url_for, session, current_app
from authlib.integrations.flask_client import OAuthError
from ..models.db import get_db_connection, create_user
from ..utils.random_username import generate_random_username
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
            random_username = generate_random_username()
            create_user(session_db, user_info['email'], random_username)
            user = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': user_info['email']}).fetchone()
    
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