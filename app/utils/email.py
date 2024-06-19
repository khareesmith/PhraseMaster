# Description: Helper functions for email-related tasks, such as sending verification emails and validating email formats.

from flask_mail import Message
import re

# Helper function to send verification emails
def send_verification_email(to, template):
    """
    Sends a verification email to the specified email address.
    
    Args:
        to: The email address to send the verification email to.
        template: The HTML template to use for the email
    
    Returns:
        None
    """
    from app import mail
    
    msg = Message('PhraseMaster: Please Verify Your Email', sender='noreply@khareesmith.com', recipients=to, html=template)
    mail.send(msg)

# Helper function to send password reset emails
def send_pass_reset_email(to, template):
    """
    Sends a password reset email to the specified email address.
    
    Args:
        to: The email address to send the verification email to.
        template: The HTML template to use for the email
    
    Returns:
        None
    """
    from app import mail
    
    msg = Message('PhraseMaster: Password Reset', sender='noreply@khareesmith.com', recipients=to, html=template)
    mail.send(msg)
    
# Helper function to validate email format
def is_valid_email(email):
    """
    Checks if the given email address is valid.
    
    Args:
        email: The email address to validate
    
    Returns:
        True if the email address is valid, False otherwise
    """
    email_regex = (
        r"^(?=.{1,256})(?=.{1,64}@.{1,255}$)"
        r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )
    return re.match(email_regex, email) is not None