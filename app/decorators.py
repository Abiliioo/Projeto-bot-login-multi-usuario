from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """
    Decorator que restringe o acesso a uma rota apenas para usuários administradores.
    Se o usuário não for administrador, retorna um erro 403 (acesso proibido).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se o usuário está autenticado e se é administrador
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Proíbe o acesso se o usuário não for administrador
        return f(*args, **kwargs)
    
    return decorated_function
