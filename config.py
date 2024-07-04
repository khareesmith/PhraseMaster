# config.py
import os
import pytz

class Config:
    """
    Configuration class for the PhraseMaster Flask application.
    """
    # Secret key for session management and other security-related needs
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'True').lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = os.environ.get('REMEMBER_COOKIE_HTTPONLY', 'True').lower() == 'true'
    
    # Session management
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'sqlalchemy')
    
    TIMEZONE = pytz.timezone('US/Eastern')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() == 'true'
    
    # OPENAI API Key
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'live.smtp.mailtrap.io')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'api')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Security configuration
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
    
    # OAuth provider configurations
    GOOGLE_OAUTH_BASE_URL = 'https://accounts.google.com/o/oauth2'
    GOOGLE_API_BASE_URL = 'https://www.googleapis.com/oauth2/v3'
    
    OAUTH_PROVIDERS = {
        # Google OAuth provider configuration
        'google': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
            'authorize_url': f'{GOOGLE_OAUTH_BASE_URL}/auth',
            'access_token_url': f'{GOOGLE_OAUTH_BASE_URL}/token',
            'userinfo_endpoint': f'{GOOGLE_API_BASE_URL}/userinfo',
            'jwks_uri': f'{GOOGLE_API_BASE_URL}/certs'
        }
        
        # Add more OAuth providers here
    }