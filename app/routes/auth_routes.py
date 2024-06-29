from flask import Blueprint
from .auth import login, pass_reset, oauth, register, profile

# Create a Blueprint for the authentication routes
auth_bp = Blueprint('auth', __name__)

# Import routes from submodules
auth_bp.add_url_rule('/login', view_func=login.login, methods=['GET', 'POST'])
auth_bp.add_url_rule('/logout', view_func=login.logout)
auth_bp.add_url_rule('/register', view_func=register.register, methods=['GET', 'POST'])
auth_bp.add_url_rule('/resend_verification', view_func=register.resend_verification, methods=['POST'])
auth_bp.add_url_rule('/confirm_email/<token>', view_func=register.confirm_email)
auth_bp.add_url_rule('/login/<provider>', view_func=oauth.login_provider, methods=['GET', 'POST'])
auth_bp.add_url_rule('/authorize/<provider>', view_func=oauth.authorize)
auth_bp.add_url_rule('/reset_password', view_func=pass_reset.reset_password_request, methods=['GET', 'POST'])
auth_bp.add_url_rule('/reset_password/<token>', view_func=pass_reset.reset_password, methods=['GET', 'POST'])
auth_bp.add_url_rule('/choose_username', view_func=profile.choose_username, methods=['GET', 'POST'])
auth_bp.add_url_rule('/generate_usernames', view_func=profile.generate_usernames, methods=['GET'])
auth_bp.add_url_rule('/change_password', view_func=profile.change_password, methods=['GET', 'POST'])