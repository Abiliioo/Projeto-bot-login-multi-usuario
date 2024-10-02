import os
from app import create_app

# Define o ambiente a partir de uma variável de ambiente, com fallback para 'development'
env = os.getenv('FLASK_ENV', 'development')  # Certifique-se de que não há comentários dentro da string

app = create_app(env)  # Define o ambiente ('production' ou 'development')
app.config['TEMPLATES_AUTO_RELOAD'] = True

if __name__ == '__main__':
    debug_mode = env == 'development'  # Apenas ativa o modo debug se for 'development'
    app.run(debug=debug_mode)
