from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate  # Importa o Flask-Migrate
from config import config
 
# Inicialização das extensões
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

def create_app(config_name='production'): 
    app = Flask(__name__)

    # Carrega as configurações do ambiente
    app.config.from_object(config[config_name])

    # Verifica se a DATABASE_URL está usando 'postgres://' e substitui por 'postgresql://'
    if 'SQLALCHEMY_DATABASE_URI' in app.config and app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://")

    # Inicializa o banco de dados e o gerenciador de login com tratamento de erros
    try:
        db.init_app(app)
    except Exception as e:
        app.logger.error(f"Erro ao inicializar o banco de dados: {e}")

    login_manager.init_app(app)

    # Inicializa o Flask-Migrate
    migrate = Migrate(app, db)  # Adiciona a integração com Flask-Migrate

    # Importação de models e User aqui, para evitar importação circular
    from .models import User

    # Função para carregar o usuário pela ID
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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
        app.logger.error(f"Erro interno no servidor: {e}")
        return render_template('500.html'), 500

    return app
