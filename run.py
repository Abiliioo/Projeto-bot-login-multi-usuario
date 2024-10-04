import os
from app import create_app

# Define o ambiente a partir de uma variável de ambiente, com fallback para 'development'
env = os.getenv('FLASK_ENV', 'development')

# Cria a aplicação Flask com o ambiente especificado ('production' ou 'development')
app = create_app(env)

# Configuração para recarregar templates automaticamente em ambiente de desenvolvimento
if env == 'development':
    app.config['TEMPLATES_AUTO_RELOAD'] = True

if __name__ == '__main__':
    # Executa o aplicativo no modo debug apenas se o ambiente for 'development'
    app.run(debug=(env == 'development'))
