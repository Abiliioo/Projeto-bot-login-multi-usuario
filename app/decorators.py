from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Proíbe o acesso se o usuário não for administrador
        return f(*args, **kwargs)
    return decorated_function
