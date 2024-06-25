from flask import Flask, session
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_mail import Mail
from flask_session import Session
from authlib.integrations.flask_client import OAuth

# Mail instance
mail = Mail()

# Create the Flask application
def create_app():
    
    """
    Create and configure the Flask application.
    """
    
    # Initialize the Flask application and load the configuration
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    csrf.init_app(app)
    
    # Initialize the Flask Session extension
    Session()
    
    # Initialize the Flask Mail extension
    mail.init_app(app)
    
    # Initialize OAuth with the application
    oauth = OAuth(app)
    for name, config in app.config['OAUTH_PROVIDERS'].items():
        oauth.register(name=name, **config)

    csp = {
    'default-src': "'self'",
    'script-src': [
        "'self'",
        "'unsafe-inline'",
        "https://kit.fontawesome.com",
        "https://cdn.jsdelivr.net",
        "https://ka-f.fontawesome.com",
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
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': [
        "'self'",
        "https://ka-f.fontawesome.com",
    ],
    }

    Talisman(app,
            content_security_policy=csp,
            content_security_policy_nonce_in=['script-src'])
    
    # Register Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.api_routes import api_bp
    from .routes.view_routes import view_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(view_bp, url_prefix='/')

    return app