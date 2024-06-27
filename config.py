# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Configuration class for the PhraseMaster Flask application.
    """
    # Secret key for session management and other security-related needs
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OPENAI API Key
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Mail configuration
    MAIL_SERVER = 'live.smtp.mailtrap.io'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'api'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Security configuration
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
    
    # OAuth provider configurations
    OAUTH_PROVIDERS = {
        'google': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
            'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
            'access_token_url': 'https://accounts.google.com/o/oauth2/token',
            'userinfo_endpoint': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'jwks_uri': 'https://www.googleapis.com/oauth2/v3/certs'
        }
        # Add other providers as needed
    }