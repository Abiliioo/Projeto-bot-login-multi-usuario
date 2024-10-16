import os
from app import create_app, db
from flask_apscheduler import APScheduler
from datetime import datetime
from app.models import Project

class Config:
    SCHEDULER_API_ENABLED = True

# Define o ambiente a partir de uma variável de ambiente, com fallback para 'development'
env = os.getenv('FLASK_ENV', 'development')

# Cria a aplicação Flask com o ambiente especificado ('production' ou 'development')
app = create_app(env)

# Adiciona a configuração do scheduler ao app
app.config.from_object(Config())

# Configuração para recarregar templates automaticamente em ambiente de desenvolvimento
if env == 'development':
    app.config['TEMPLATES_AUTO_RELOAD'] = True

# Inicializa o APScheduler
scheduler = APScheduler()

@scheduler.task('interval', hours=12)
def delete_old_projects_task():
    """
    Tarefa agendada para excluir projetos antigos a cada 12 horas.
    Garantindo que o contexto de aplicação esteja ativo.
    """
    with app.app_context():
        Project.delete_old_projects()
        print(f"[{datetime.now()}] Projetos antigos deletados com sucesso.")

# Inicializa o agendamento no app Flask
scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    # Executa o aplicativo no modo debug apenas se o ambiente for 'development'
    app.run(debug=(env == 'development'))
