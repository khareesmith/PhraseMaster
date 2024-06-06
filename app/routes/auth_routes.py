from flask import Blueprint, redirect, url_for, session, current_app, render_template, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import validate_csrf
from authlib.integrations.flask_client import OAuthError
from ..models.db import get_db_connection, update_username, User
from ..utils.random_username import generate_random_usernames
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
import bleach

auth_bp = Blueprint('auth', __name__)

# Registration route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        validate_csrf(request.form.get('csrf_token'))
        
        # Validate and sanitize email and password
        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        
        # Validate email and password
        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        
        session_db = get_db_connection()
        try:
            user = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email}).fetchone()
            if user:
                flash('Email address already registered', "error")
                return render_template('register.html')
            
            session_db.execute(text('INSERT INTO users (email, password) VALUES (:email, :password)'), {'email': email, 'password': hashed_password})
            session_db.commit()
            
            session['pending_user'] = {'email': email}
            random_usernames = generate_random_usernames()
            session['pending_user'] = {'email': email, 'usernames': random_usernames}
            session.modified = True
            return redirect(url_for('auth.choose_username'))
        
        except SQLAlchemyError as e:
            print(f"Database Error: {e}")
            session_db.rollback()
            return "Database error", 500
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':      
        validate_csrf(request.form.get('csrf_token'))
        
        # Validate and sanitize email and password
        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        
        if not email or not password:
            flash('Email and password are required', "error")
            return redirect(url_for('auth.login'))
        
        session_db = get_db_connection()
        try:
            result = session_db.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email})
            user = result.fetchone()
            
            if not user:
                flash('User does not exist. Please register.', "error")
                return redirect(url_for('auth.login'))
            
            if user:
                user = dict(zip(result.keys(), user))
            
            if user and check_password_hash(user['password'], password):
                session['user'] = {'id': user['id'], 'name': user['name'], 'email': user['email']}
                session.modified = True 
                return redirect(url_for('view.index'))
            else:
                flash('Invalid email or password', "error")
                return redirect(url_for('auth.login'))
        except SQLAlchemyError as e:
            print(f"Database Error: {e}")
            return "Database error", 500
    return render_template('login.html')

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
            new_user = User(email=resp['email'], name=None)
            session_db.add(new_user)
            session_db.commit()  # Ensure user is committed to the database
            user = new_user
            session['pending_user'] = {'email': resp['email'], 'usernames': generate_random_usernames()}
            return redirect(url_for('auth.choose_username'))
    
        if user:
            user = dict(zip(result.keys(), user))  # Convert result to dictionary
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
    print("Inside choose_username route")
    """Display username choices and handle the selection."""
    
    # Check if a user is logged in
    user = session.get('user')
    print(f"User is logged in: {user}")
    pending_user = session.get('pending_user')
    print(f"Pending user: {pending_user}")
    
    if request.method == 'POST':

        validate_csrf(request.form.get('csrf_token'))
        # Validate and sanitize username
        username = bleach.clean(request.form['username'])
        print(f"Username: {username}")
        
        if pending_user:
            email = pending_user.get('email')
            print(f"Email for Pending User: {email}")
        elif user:
            email = user.get('email')
            print(f"Email for User: {email}")
        else:
            return redirect(url_for('auth.login'))

        session_db = get_db_connection()
        try:
            with session_db.no_autoflush:
                user_record = session_db.query(User).filter_by(email=email).one()
                print(f"User record: {user_record}")
            
                if user_record:
                    user_id = user_record.id
                    old_username = user_record.name
                    print(f"Old username: {old_username}")
                    user_record.name = username
                    
                    # Update submissions with the new username
                    session_db.execute(text("UPDATE submissions SET username = :new_username WHERE user_id = :user_id"), {'new_username': username, 'user_id': user_id})
                
            session_db.commit()
            
            session['pending_user']['username'] = username
            session['user'] = {'id': user_id, 'name': user_record.name, 'email': email} # Set user session
            session.pop('pending_user', None)
            session.modified = True  # Ensure session is marked as modified
            return redirect(url_for('view.index'))
        
        except SQLAlchemyError as e:
            print(f"Database Error: {e}")  # Log the error for debugging
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

    return render_template('choose_username.html', usernames=usernames)

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

@auth_bp.route('/update_username', methods=['GET', 'POST'])

def update_username():
    print("Inside update_username route")

    # """Update the user's username."""
    # validate_csrf(request.form.get('csrf_token'))
    
    def set_foreign_key_checks(dbsession, enable=True):
        dbsession.execute(text(f"SET session_replication_role = {'DEFAULT' if enable else 'REPLICA'}"))
    
    new_username = request.form.get('new_username')
    user = session.get('user')
    
    if not user:
        return redirect(url_for('auth.login'))
    
    email = user['email']
    old_username = user['name']
    
    session_db = get_db_connection()
    try:
        # Begin a transaction
        with session_db.begin():
            # Temporarily disable foreign key checks
            set_foreign_key_checks(session_db, enable=False)
            print("Disabled foreign key checks")

            # Update the submissions associated with this user first
            session_db.execute(text('UPDATE submissions SET username = :new_username WHERE username = :old_username'), {'new_username': new_username, 'old_username': old_username})
            print("Updated submissions successfully")

            # Then, update the username in the users table
            session_db.execute(text('UPDATE users SET name = :name WHERE email = :email'), {'name': new_username, 'email': email})
            print("Updated users successfully")
            
            # Re-enable foreign key checks
            set_foreign_key_checks(session_db, enable=True)
            print("Re-enabled foreign key checks")

        # Commit the transaction
        session_db.commit()
        print("Transaction committed successfully")
        
        # Update session with new username
        session['user']['name'] = new_username
        session.modified = True
        
        flash('Username updated successfully', 'success')
        return redirect(url_for('view.profile'))
    
    except SQLAlchemyError as e:
        print(f"Database Error: {e}")
        session_db.rollback()
        flash('An error occurred while updating your username. Please try again.', 'error')
        return redirect(url_for('view.profile'))

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
        
        if not user_record or user_record['password'] is None:
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
            
            if not check_password_hash(user_record['password'], current_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('auth.change_password'))
            
            hashed_password = generate_password_hash(new_password)
            session_db.execute(text('UPDATE users SET password = :password WHERE email = :email'), {'password': hashed_password, 'email': user['email']})
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
    
    return render_template('change_password.html')


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