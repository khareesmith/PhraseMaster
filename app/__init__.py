from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_mail import Mail
from flask_session import Session
from authlib.integrations.flask_client import OAuth
from config import Config

# Mail instance
mail = Mail()

# CSRF protection
csrf = CSRFProtect()

# Database connection
db = SQLAlchemy()

def register_blueprints(app):
    from app.routes import auth_bp, api_bp, view_bp
    blueprints = [
        (auth_bp, '/auth'),
        (api_bp, '/api'),
        (view_bp, '/'),
    ]
    for blueprint, url_prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)

def configure_csp(app):
    csp = {
    'default-src': "'self'",
    'script-src': [
        "'self'",
        "'unsafe-inline'",
        "https://kit.fontawesome.com",
        "https://cdn.jsdelivr.net",
        "https://ka-f.fontawesome.com",
        "https://accounts.google.com",
        "https://apis.google.com",
        "https://cdnjs.cloudflare.com",
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
        "https://ka-f.fontawesome.com",
    ],
    'font-src': [
        "'self'",
        "https://fonts.gstatic.com",
        "https://ka-f.fontawesome.com",
    ],
    'img-src': ["'self'", "data:", "https:", "https://accounts.google.com"],
    'connect-src': [
        "'self'",
        "https://ka-f.fontawesome.com",
        "https://accounts.google.com",
    ],
    'frame-src': [
        "'self'",
        "https://accounts.google.com",
    ],
    'form-action': ["'self'", "https://accounts.google.com"],
    }

    Talisman(app,
            content_security_policy=csp,
            content_security_policy_nonce_in=['script-src'])

# Create the Flask application
def create_app(config_class=Config):
    
    # Initialize the Flask application
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Register Blueprints
    register_blueprints(app)

    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Initialize Talisman
    configure_csp(app)
    
    # Initialize the Flask SQLAlchemy extension
    db.init_app(app)
    app.config['SESSION_SQLALCHEMY'] = db
    
    # Initialize the Flask Session extension
    Session(app)
    
    # Initialize the Flask Mail extension
    mail.init_app(app)
    
    # Initialize OAuth with the application
    oauth = OAuth(app)
    for name, config in app.config['OAUTH_PROVIDERS'].items():
        oauth.register(name=name, **config)

    return app