from functools import wraps
from flask import redirect, url_for, abort, jsonify, request
from flask_login import current_user


def admin_required(f):
    """
    Decorator that restricts access to admin users only.
    
    For HTML routes: redirects to login if not authenticated, or 403 if not admin.
    For API endpoints: returns 403 JSON response if not admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.login', next=request.path))
        
        if not current_user.is_admin():
            # Check if this is an API call (X-Requested-With header)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'ok': False, 'message': 'Access denied. Admin privileges required.'}), 403
            
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def founder_required(f):
    """Restrict account-role management to the configured founder account."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.login', next=request.path))
        from flask import current_app
        if current_user.email.lower() != current_app.config['FOUNDER_EMAIL']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
