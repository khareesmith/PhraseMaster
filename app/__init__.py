from flask import Flask
from flask_session import Session
from authlib.integrations.flask_client import OAuth

from .routes.auth_routes import auth_bp
from .routes.api_routes import api_bp
from .routes.view_routes import view_bp

def create_app():
    
    """
    Create and configure the Flask application.
    """
    
    app = Flask(__name__)
    app.config.from_object('config.Config')
    Session()
    

    # Initialize OAuth with the application
    oauth = OAuth(app)
    for name, config in app.config['OAUTH_PROVIDERS'].items():
        oauth.register(name=name, **config)
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(view_bp, url_prefix='/')

    return app