from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
from typing import Union

def generate_confirmation_token(email: str) -> str:
    """
    Generate a confirmation token for the provided email.

    Args:
        email (str): The email address to generate the token for.

    Returns:
        str: The generated confirmation token.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token: str, expiration: int = 3600) -> Union[str, bool]:
    """
    Confirm the provided token and return the email if valid.

    Args:
        token (str): The token to confirm.
        expiration (int, optional): The expiration time for the token in seconds. Defaults to 3600 (1 hour).

    Returns:
        Union[str, bool]: The email address if the token is valid, False otherwise.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except (SignatureExpired, BadSignature):
        return False
    return email