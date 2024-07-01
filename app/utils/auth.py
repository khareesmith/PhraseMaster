from flask import jsonify, session, redirect, url_for, flash
from app.models.db import User, get_db_connection
from functools import wraps
from typing import Callable, Any
from zxcvbn import zxcvbn

# Decorator to require login
def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to protect routes that require authentication.

    Args:
        f (Callable): The function to be decorated.

    Returns:
        Callable: The decorated function.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user' not in session:
            return jsonify({'error': 'You must be logged in to perform this action.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Decorator to require admin privileges
def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to protect routes that require admin privileges.

    Args:
        f (Callable): The function to be decorated.

    Returns:
        Callable: The decorated function.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user' not in session:
            flash('You need to be logged in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        user_id = session['user'].get('id')
        session_db = get_db_connection()
        
        try:
            user = session_db.query(User).filter_by(id=user_id).first()
            if not user or not user.is_admin:
                flash('You need to be an admin to access this page.', 'error')
                return redirect(url_for('view.index'))
        finally:
            session_db.close()
        
        return f(*args, **kwargs)
    return decorated_function

# Helper function to check password strength
def is_strong_password(password: str) -> dict:
    """
    Check password strength using the zxcvbn library.

    Args:
        password (str): The password to check.

    Returns:
        dict: The zxcvbn result object containing password strength information.

    Raises:
        ValueError: If the password is empty or not a string.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string")

    return zxcvbn(password)