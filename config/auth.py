"""Authentication configuration module - imports from db.auth"""
from db.auth import (
    verify_user,
    create_user,
    login_user,
    logout_user,
    init_auth_tables,
    require_auth,
    get_current_user_id,
    request_password_reset,
    reset_password_with_otp,
    redirect_to_login,
    redirect_to_home,
    hide_default_sidebar_nav,
    render_authenticated_sidebar,
)

__all__ = [
    'verify_user',
    'create_user',
    'login_user',
    'logout_user',
    'init_auth_tables',
    'require_auth',
    'get_current_user_id',
    'request_password_reset',
    'reset_password_with_otp',
    'redirect_to_login',
    'redirect_to_home',
    'hide_default_sidebar_nav',
    'render_authenticated_sidebar',
]

