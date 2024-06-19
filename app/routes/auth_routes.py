from flask import Blueprint, redirect, url_for, session, current_app, render_template, request, flash
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

# Create a Blueprint for the authentication routes
auth_bp = Blueprint('auth', __name__)

# Registration route
@auth_bp.route('/register', methods=['GET', 'POST'])
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
            return "Database error", 500
        
    return render_template('auth/register.html')

# Email confirmation route
@auth_bp.route('/confirm/<token>', methods=['GET', 'POST'])
# Confirm the token and update the user's email_verified status
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

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
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
            
            # Dictionary mapping column names
            user_dict = dict(zip(result.keys(), user))
            
            # Check if the user has verified their email
            if not user_dict['email_verified']:
                flash('Please verify your email address before logging in.', 'error')
                session['unverified_user'] = user_dict['email']
                return render_template('auth/login.html', unverified=True)
            
            # Create a User object from the dictionary
            db_user = User(
                id=user_dict['id'],
                email=user_dict['email'],
                password_hash=user_dict['password_hash'],
                password_salt=user_dict['password_salt'],
                name=user_dict['name'],
                total_votes=user_dict['total_votes'],
                email_verified=user_dict['email_verified']
            )
            
            # Check the password and redirect to choose_username if the user has not set a name
            if db_user.check_password(password):
                session['user'] = {'id': db_user.id, 'name': db_user.name, 'email': db_user.email}
                session.modified = True
                if db_user.name is None:
                    return redirect(url_for('auth.choose_username'))
                return redirect(url_for('view.index'))
            else:
                flash('Invalid email or password', "error")
                return redirect(url_for('auth.login'))
        
        # Handle database errors
        except SQLAlchemyError as e:
            flash(f"An error occurred while processing your request: {e}", "error")
            return render_template('auth/login.html')
    return render_template('auth/login.html')

# OAuth login route (Google right now)
@auth_bp.route('/login/<provider>', methods=['GET', 'POST'])
def login_provider(provider):
    """
    Initiate the OAuth login process for the specified provider.
    """
    oauth_provider = current_app.extensions['authlib.integrations.flask_client'].create_client(provider)
    redirect_uri = url_for('auth.authorize', provider=provider, _external=True)
    return oauth_provider.authorize_redirect(redirect_uri, scope='openid email profile')

# OAuth callback route (Google right now)
@auth_bp.route('/authorize/<provider>')
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
        user = result.fetchone()
        
        # Create a new user if the user does not exist
        if not user:
            random_password = User.generate_random_password()
            new_user = User(email=resp['email'], name=None, google_user=True)
            new_user.set_password(random_password)
            session_db.add(new_user)
            session_db.commit()
            user = new_user
            session['pending_user'] = {'email': resp['email'], 'usernames': generate_random_usernames()}
            return redirect(url_for('auth.choose_username'))
        
        # Log in the user if they exist
        if user:
            user = dict(zip(result.keys(), user))
            session['user'] = {'id': user['id'], 'name': user['name'], 'email': user['email']}
            session.modified = True
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

# Username selection route
@auth_bp.route('/choose_username', methods=['GET', 'POST'])
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

    return render_template('profile/choose_username.html', usernames=usernames)

# Generate new random usernames route
@auth_bp.route('/generate_usernames')
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

# Change password route
@auth_bp.route('/change_password', methods=['GET', 'POST'])
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

# Resend verification email route
@auth_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
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
                flash('A new verification email has been sent.', 'success')
            else:
                flash('User not found or already verified.', 'error')
    
    # Handle database errors
    except SQLAlchemyError as e:
        session_db.rollback()
        flash(f"An error occurred: {e}", 'error')
        return "Database error", 500
    
    return redirect(url_for('auth.login'))

# Reset password request route
@auth_bp.route('/reset_password', methods=['GET', 'POST'])
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
                send_verification_email([email], html)
                flash('A password reset email has been sent.', 'success')
            else:
                flash('Email not found.', 'error')
                return redirect(url_for('auth.reset_password_request'))
                
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_req.html')

# Reset password route
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
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

# Logout route
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