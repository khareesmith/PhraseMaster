from flask import Blueprint, redirect, url_for, session, current_app, render_template, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import validate_csrf, CSRFError
from authlib.integrations.flask_client import OAuthError
from ..models.db import get_db_connection, User
from ..utils.random_username import generate_random_usernames
from ..utils.email import send_verification_email, is_valid_email
from ..utils.token import generate_confirmation_token, confirm_token
from ..utils.auth import is_strong_password
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
import bleach

auth_bp = Blueprint('auth', __name__)

# Registration route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
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
                
                token = generate_confirmation_token(new_user.email)
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                html = render_template('auth/confirm_email.html', confirm_url=confirm_url)
                send_verification_email([new_user.email], html)
            
                flash('A verification email has been sent to your email address.', 'success')
                return redirect(url_for('auth.login'))
                # random_usernames = generate_random_usernames()
                # session['pending_user'] = {'email': email, 'usernames': random_usernames}
                # session.modified = True
                # return redirect(url_for('auth.choose_username'))
        
        except SQLAlchemyError as e:
            print(f"Database Error: {e}")
            session_db.rollback()
            return "Database error", 500
        
    return render_template('auth/register.html')

@auth_bp.route('/confirm/<token>', methods=['GET', 'POST'])
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
        
        if user is None:
            flash('Account not found.', 'error')
            return redirect(url_for('auth.register'))

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

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':      
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash("Invalid CSRF token", "error")
            return render_template('auth/login.html')
        
        # Validate and sanitize email and password
        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        
        if not email or not password:
            flash('Email and password are required', "error")
            return redirect(url_for('auth.login'))
        try:
            with get_db_connection() as session_db:
                result = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email})
                user = result.fetchone()
            
            if not user:
                flash('User does not exist. Please register.', "error")
                return redirect(url_for('auth.login'))
            
            user_dict = dict(zip(result.keys(), user))
            
            if not user_dict['email_verified']:
                flash('Please verify your email address before logging in.', 'error')
                session['unverified_user'] = user_dict['email']
                return render_template('auth/login.html', unverified=True)
            
            db_user = User(
                id=user_dict['id'],
                email=user_dict['email'],
                password_hash=user_dict['password_hash'],
                name=user_dict['name'],
                total_votes=user_dict['total_votes'],
                email_verified=user_dict['email_verified']
            )
            
            if db_user.check_password(password):
                session['user'] = {'id': db_user.id, 'name': db_user.name, 'email': db_user.email}
                session.modified = True
                if db_user.name is None:
                    # random_usernames = generate_random_usernames()
                    # session['pending_user'] = {'email': email, 'usernames': random_usernames}
                    return redirect(url_for('auth.choose_username'))
                return redirect(url_for('view.index'))
            else:
                flash('Invalid email or password', "error")
                return redirect(url_for('auth.login'))
        except SQLAlchemyError as e:
            flash(f"An error occurred while processing your request: {e}", "error")
            return render_template('auth/login.html')
    return render_template('auth/login.html')

@auth_bp.route('/login/<provider>', methods=['GET', 'POST'])
def login_provider(provider):
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
        resp = oauth_provider.userinfo()
        
        # Sanitize user_info fields
        email = bleach.clean(resp['email'])
        if not email:
            flash('Failed to retrieve email from Google', "error")
            return redirect(url_for('auth.login'))
        
    except OAuthError as error:
        print(f"OAuth Error: {error}")  # Log the error for debugging
        return "Authorization failed", 500
    
    # Implement user creation or retrieval logic
    session_db = get_db_connection()
    try:
        result = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': resp['email']})
        user = result.fetchone()
        
        if not user:
            random_password = User.generate_random_password()
            new_user = User(email=resp['email'], name=None, google_user=True)
            new_user.set_password(random_password)
            session_db.add(new_user)
            session_db.commit()
            user = new_user
            session['pending_user'] = {'email': resp['email'], 'usernames': generate_random_usernames()}
            return redirect(url_for('auth.choose_username'))
    
        if user:
            user = dict(zip(result.keys(), user))
            session['user'] = {'id': user['id'], 'name': user['name'], 'email': user['email']}
            session.modified = True
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
    
    # Check if a user is logged in
    user = session.get('user')
    pending_user = session.get('pending_user')
    
    if request.method == 'POST':

        validate_csrf(request.form.get('csrf_token'))
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
            
                if user_record:
                    user_id = user_record.id
                    user_record.name = username
                    
                    # Update submissions with the new username
                    session_db.execute(text("UPDATE submissions SET username = :new_username WHERE user_id = :user_id"), {'new_username': username, 'user_id': user_id})
                
            session_db.commit()
            
            session['pending_user']['username'] = username
            session['user'] = {'id': user_id, 'name': user_record.name, 'email': email}
            session.pop('pending_user', None)
            session.modified = True
            return redirect(url_for('view.index'))
        
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

    return render_template('profile/choose_username.html', usernames=usernames)

@auth_bp.route('/generate_usernames')
def generate_usernames():
    """Generate new random usernames and update the session."""
    pending_user = session.get('pending_user')
    
    if not pending_user:
        return redirect(url_for('auth.login'))
    
    random_usernames = generate_random_usernames()
    session['pending_user']['usernames'] = random_usernames
    session.modified = True  # Mark the session as modified to ensure changes are saved
    return redirect(url_for('auth.choose_username'))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    """Allow users to change their password."""
    user = session.get('user')
    
    if not user:
        return redirect(url_for('auth.login'))
    
    session_db = get_db_connection()
    try:
        result = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': user['email']}).fetchone()
        
        if result:
            user_record = result._mapping
        else:
            user_record = None
        
        if not user_record or user_record['google_user']:
            flash('You cannot change your password here. Please use Google to manage your account.', 'error')
            return redirect(url_for('view.profile'))
        
        if request.method == 'POST':
            validate_csrf(request.form.get('csrf_token'))
            current_password = bleach.clean(request.form['current_password'])
            new_password = bleach.clean(request.form['new_password'])
            confirm_password = bleach.clean(request.form['confirm_password'])
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return redirect(url_for('auth.change_password'))
            
            if current_password == new_password:
                flash('New password must be different from the current password', 'error')
                return redirect(url_for('auth.change_password'))
            
            if not check_password_hash(user_record['password_hash'], current_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('auth.change_password'))
            
            hashed_password = generate_password_hash(new_password)
            session_db.execute(text('UPDATE users SET password_hash = :password_hash WHERE email = :email'), {'password_hash': hashed_password, 'email': user['email']})
            session_db.commit()
            
            flash('Password updated successfully', 'success')
            return redirect(url_for('view.profile'))
    except SQLAlchemyError as e:
        print(f"Database Error: {e}")
        session_db.rollback()
        flash('An error occurred while updating your password. Please try again.', 'error')
        return redirect(url_for('auth.change_password'))
    finally:
        session_db.close()
    
    return render_template('profile/change_password.html')

@auth_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    try:
        validate_csrf(request.form.get('csrf_token'))
    except CSRFError:
        flash("Invalid CSRF token", "error")
        return redirect(url_for('auth.login'))
    
    email = session.get('unverified_user')
    if not email:
        flash('No unverified email found.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        with get_db_connection() as session_db:
            user = session_db.execute(
                text('SELECT * FROM users WHERE email = :email'), {'email': email}
            ).fetchone()
            
            if user and not user.email_verified:
                token = generate_confirmation_token(email)
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                html = render_template('auth/confirm_email.html', confirm_url=confirm_url)
                send_verification_email([email], html)
                flash('A new verification email has been sent.', 'success')
            else:
                flash('User not found or already verified.', 'error')
    except SQLAlchemyError as e:
        flash(f"An error occurred: {e}", 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
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