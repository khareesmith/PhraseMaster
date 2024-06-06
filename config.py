# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    """
    Configuration class for the PhraseMaster Flask application.
    """
    # Secret key for session management and other security-related needs
    SECRET_KEY = os.getenv('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    DEBUG = True
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OPENAI API Key
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # OAuth provider configurations
    OAUTH_PROVIDERS = {
        'google': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
            'access_token_url': 'https://accounts.google.com/o/oauth2/token',
            'userinfo_endpoint': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'jwks_uri': 'https://www.googleapis.com/oauth2/v3/certs'
            # 'redirect_uri': 'http://localhost:5000/auth/authorize/google'
        }
        # Add other providers as needed
    }