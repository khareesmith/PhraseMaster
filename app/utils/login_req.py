from flask import jsonify, session
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'You must be logged in to perform this action.'}), 403
        return f(*args, **kwargs)
    return decorated_function