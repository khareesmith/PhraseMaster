from .auth_routes import auth_bp
from .api_routes import api_bp
from .view_routes import view_bp

__all__ = ['auth_bp', 'api_bp', 'view_bp']