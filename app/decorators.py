from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user
import logging

def admin_required(f):
    """
    Decorator que restringe o acesso a uma rota apenas para usuários administradores.
    Se o usuário não for administrador, retorna um erro 403 (acesso proibido) e exibe uma mensagem de erro.
    
    Uso:
    @admin_required
    def my_view():
        ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se o usuário está autenticado
        if not current_user.is_authenticated:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))

        # Verifica se o usuário é administrador
        if not current_user.is_admin:
            flash('Você não tem permissão para acessar esta página.', 'danger')
            logging.warning(f"Tentativa de acesso não autorizado pelo usuário {current_user.username}.")
            abort(403)  # Proíbe o acesso se o usuário não for administrador

        return f(*args, **kwargs)
    
    return decorated_function
