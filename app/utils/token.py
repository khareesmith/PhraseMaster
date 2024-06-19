# Description: Token generation and verification functions

from itsdangerous import URLSafeTimedSerializer
from flask import current_app

# Generate a confirmation token for the provided email
def generate_confirmation_token(email):
    """
    Generate a confirmation token for the provided email.
    
    Args:
        email (str): The email address to generate the token for.
    
    Returns:
        str: The generated confirmation token.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

# Confirm the provided token and return the email if valid
def confirm_token(token, expiration=3600):
    """
    Confirm the provided token and return the email if valid.
    
    Args:
        token (str): The token to confirm.
        expiration (int): The expiration time for the token.
        
    Returns:
        str: The email address if the token is valid, False otherwise.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email