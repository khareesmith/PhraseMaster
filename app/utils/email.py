# Description: Helper functions for email-related tasks, such as sending verification emails and validating email formats.

from flask_mail import Message
import re

# Helper function to send verification emails
def send_verification_email(to, template):
    from app import mail
    
    # token = User.get_verification_token(user)
    msg = Message('Email Verification', sender='mailtrap@khareesmith.com', recipients=to, html=template)
    mail.send(msg)

# Helper function to validate email format
def is_valid_email(email):
    email_regex = (
        r"^(?=.{1,256})(?=.{1,64}@.{1,255}$)"
        r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )
    return re.match(email_regex, email) is not None

# TO DO: Helper function to send password reset emails