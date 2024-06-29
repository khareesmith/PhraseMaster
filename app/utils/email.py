from flask_mail import Message
from flask import current_app
import re
from typing import List

EMAIL_REGEX = re.compile(r"^(?=.{1,256})(?=.{1,64}@.{1,255}$)"
                        r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Helper function to send verification emails
def send_verification_email(to: List[str], template: str) -> None:
    """
    Sends a verification email to the specified email address.

    Args:
        to (List[str]): The email address(es) to send the verification email to.
        template (str): The HTML template to use for the email.

    Raises:
        Exception: If there's an error sending the email.
    """
    try:
        msg = Message('PhraseCraze: Please Verify Your Email',
                    sender='noreply@khareesmith.com',
                    recipients=to,
                    html=template)
        current_app.extensions['mail'].send(msg)
    except Exception as e:
        current_app.logger.error(f"Error sending verification email: {e}")
        raise

# Helper function to send password reset emails
def send_pass_reset_email(to: List[str], template: str) -> None:
    """
    Sends a password reset email to the specified email address.

    Args:
        to (List[str]): The email address(es) to send the password reset email to.
        template (str): The HTML template to use for the email.

    Raises:
        Exception: If there's an error sending the email.
    """
    try:
        msg = Message('PhraseCraze: Password Reset',
                    sender='noreply@khareesmith.com',
                    recipients=to,
                    html=template)
        current_app.extensions['mail'].send(msg)
    except Exception as e:
        current_app.logger.error(f"Error sending password reset email: {e}")
        raise
    
# Helper function to validate email format
def is_valid_email(email: str) -> bool:
    """
    Checks if the given email address is valid.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email address is valid, False otherwise.
    """
    return EMAIL_REGEX.match(email) is not None