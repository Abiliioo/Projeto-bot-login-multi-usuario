from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
import logging

# Inicialização das extensões
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

def create_app(config_name='production'): 
    app = Flask(__name__)

    # Carrega as configurações do ambiente
    try:
        app.config.from_object(config[config_name])
    except Exception as e:
        app.logger.error(f"Erro ao carregar as configurações: {e}")
        raise

    # Verifica e corrige a URI do PostgreSQL (compatível com Heroku)
    if 'SQLALCHEMY_DATABASE_URI' in app.config:
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith("postgres://"):
            try:
                app.config['SQLALCHEMY_DATABASE_URI'] = db_uri.replace("postgres://", "postgresql://")
                app.logger.info("SQLALCHEMY_DATABASE_URI ajustada para postgresql://")
            except Exception as e:
                app.logger.error(f"Erro ao ajustar a URI do PostgreSQL: {e}")
                raise

    # Inicializa o banco de dados com tratamento de erros
    try:
        db.init_app(app)
        app.logger.info("Banco de dados inicializado com sucesso.")
    except Exception as e:
        app.logger.error(f"Erro ao inicializar o banco de dados: {e}")
        raise

    # Inicializa o login manager
    try:
        login_manager.init_app(app)
        app.logger.info("Login manager inicializado com sucesso.")
    except Exception as e:
        app.logger.error(f"Erro ao inicializar o login manager: {e}")
        raise

    # Inicializa o Flask-Migrate
    migrate = Migrate(app, db)

    # Importação de models
    from .models import User

    # Função para carregar o usuário pela ID
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Erro ao carregar o usuário com ID {user_id}: {e}")
            return None

    # Registro dos blueprints (módulos da aplicação)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Tratamento de erros (páginas customizadas para erros 404 e 500)
    @app.errorhandler(404)
    def page_not_found(e):
        app.logger.warning(f"Página não encontrada: {e}")
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Erro interno no servidor: {e}", exc_info=True)
        return render_template('500.html'), 500

    return app
