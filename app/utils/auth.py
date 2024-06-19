# Description: Helper functions for authentication and authorization.

from flask import jsonify, session
from functools import wraps
from zxcvbn import zxcvbn

# Decorator to require login
def login_required(f):
    """
    Login required decorator to protect routes that require authentication.
    
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'You must be logged in to perform this action.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Helper function to check password strength
def is_strong_password(password):
    """
    Check password strength using the zxcvbn library.
    
    Args:
        password: The password to check
    
    Returns:
        The zxcvbn result object
    """
    result = zxcvbn(password)
    return result