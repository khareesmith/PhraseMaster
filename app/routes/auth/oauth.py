from flask import redirect, url_for, session, current_app, flash
from authlib.integrations.flask_client import OAuthError
from sqlalchemy.exc import SQLAlchemyError
from app.models.db import get_db_connection, User
from app.utils.random_username import generate_random_usernames
from app.utils.streaks import update_login_streak
from sqlalchemy import text
import bleach

def login_provider(provider):
    """
    Initiate the OAuth login process for the specified provider.
    """
    oauth_provider = current_app.extensions['authlib.integrations.flask_client'].create_client(provider)
    redirect_uri = url_for('auth.authorize', provider=provider, _external=True)
    return oauth_provider.authorize_redirect(redirect_uri, scope='openid email profile')

def authorize(provider):
    """
    Handle the callback from the OAuth provider and log in or create the user.
    """
    # Store the OAuth provider in the session
    session['oauth_provider'] = provider
    try:
        # Create the OAuth provider client
        oauth_provider = current_app.extensions['authlib.integrations.flask_client'].create_client(provider)
        token = oauth_provider.authorize_access_token()
        resp = oauth_provider.userinfo()
        
        # Sanitize user_info fields
        email = bleach.clean(resp['email'])
        if not email:
            flash('Failed to retrieve email from Google', "error")
            return redirect(url_for('auth.login'))
    
    # Handle OAuth errors
    except OAuthError as error:
        print(f"OAuth Error: {error}")
        return "Authorization failed", 500
    
    # Check if the user exists in the database and log in or create the user
    session_db = get_db_connection()
    try:
        result = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': resp['email']})
        user_record = result.fetchone()
        
        # Create a new user if the user does not exist
        if not user_record:
            pw = User.generate_random_password()
            new_user = User(email=resp['email'], name=None, google_user=True)
            new_user.set_password(pw)
            session_db.add(new_user)
            session_db.commit()
            user = new_user
            session['pending_user'] = {'email': resp['email'], 'usernames': generate_random_usernames()}
            return redirect(url_for('auth.choose_username'))
        
        # Log in the user if they exist
        if user_record:
            user_dict = user_record._mapping
            user = session_db.query(User).filter_by(id=user_dict['id']).first()
            session['user'] = {'id': user.id, 'name': user.name, 'email': user.email}
            session.modified = True
            update_login_streak(user, session_db)
            session_db.commit()
            return redirect(url_for('view.index'))
        else:
            session_db.rollback()
            return "User creation or retrieval failed", 500

    # Handle database errors
    except SQLAlchemyError as e:
        session_db.rollback()
        print(f"SQLAlchemy Error: {e}")
        return "Database error", 500
    finally:
        session_db.close()