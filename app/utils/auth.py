from flask import jsonify, session
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