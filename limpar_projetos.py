from app import create_app, db
from app.models import Project
import logging

# Inicializando o aplicativo Flask
app = create_app()

# Configurando o logger para ver a saída no console
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def limpar_projetos():
    """
    Remove todos os projetos da tabela Project.
    """
    try:
        with app.app_context():
            num_rows_deleted = db.session.query(Project).delete()
            db.session.commit()
            logger.info(f"{num_rows_deleted} projetos removidos do banco de dados.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao limpar os projetos: {e}")

if __name__ == '__main__':
    limpar_projetos()
