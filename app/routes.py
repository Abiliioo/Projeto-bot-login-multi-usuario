import os
import requests
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from .models import Keyword, User
from . import db
from flask import Blueprint
from .decorators import admin_required
from .bot import VerificadorDeProjetos
from datetime import datetime
import logging

# Definindo o blueprint "main"
main = Blueprint('main', __name__)

# Configurando o logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Inicialização global do bot (uma instância global para manter o estado)
verificador = VerificadorDeProjetos()

# Carrega o token do bot a partir do arquivo .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    logger.error("Erro: TELEGRAM_TOKEN não encontrado. Verifique o arquivo .env.")

@main.route('/')
def home():
    """Página inicial (landing page)"""
    return render_template('index.html')

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Exibe o painel de controle para usuários comuns e admin."""
    if request.method == 'POST':
        keywords_input = request.form.get('keyword')
        if keywords_input:
            save_keywords(keywords_input)

    if current_user.is_admin:
        return redirect(url_for('main.admin_dashboard'))

    # Busca as palavras-chave do usuário
    keywords = Keyword.query.filter_by(user_id=current_user.id).all()

    # Gera o ano atual para o rodapé
    current_year = datetime.now().year
    return render_template('dashboard.html', keywords=keywords, current_year=current_year)


def save_keywords(keywords_input):
    """Salva as palavras-chave no banco de dados."""
    keywords_list = [keyword.strip() for keyword in keywords_input.split(',') if keyword.strip()]
    for keyword in keywords_list:
        existing_keyword = Keyword.query.filter_by(keyword=keyword, user_id=current_user.id).first()
        if not existing_keyword:
            new_keyword = Keyword(keyword=keyword, user_id=current_user.id)
            db.session.add(new_keyword)
    try:
        db.session.commit()
        flash('Palavras-chave salvas com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar as palavras-chave: {e}', 'danger')
        logger.error(f"Erro ao salvar palavras-chave: {e}")


@main.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    keywords = Keyword.query.filter_by(user_id=current_user.id).all()
    return render_template('admin.html', users=users, keywords=keywords)

# Controle do bot: Iniciar e parar bot
@main.route('/start_bot', methods=['POST'])
@login_required
def start_bot():
    """
    Rota para iniciar o bot.
    """
    logger.info(f"Iniciando bot para o usuário {current_user.username}")
    total_pages = 5  # Número de páginas para verificar (exemplo)
    keywords = [keyword.keyword for keyword in current_user.keywords]  # Palavras-chave do usuário atual
    bot_token = TELEGRAM_TOKEN  # Carrega o token do bot
    chat_id = current_user.chat_id  # ID do chat do Telegram do usuário
    user_id = current_user.id  # ID do usuário atual

    if not chat_id:
        logger.error(f"Usuário {current_user.username} não tem chat_id associado.")
        return jsonify({'status': 'Chat ID não associado. Por favor, inicie o bot no Telegram com /start.'}), 400

    if not verificador.bot_ativo:
        verificador.iniciar_verificacao(total_pages, keywords, bot_token, chat_id, user_id)
        logger.info(f"Bot iniciado para o usuário {current_user.username}.")
        return jsonify({'status': 'Bot iniciado com sucesso!'}), 200
    else:
        logger.info("Bot já está em execução.")
        return jsonify({'status': 'Bot já está em execução.'}), 200

@main.route('/stop_bot', methods=['POST'])
@login_required
def stop_bot():
    verificador.parar_verificacao()
    logger.info(f"Bot parado para o usuário {current_user.username}.")
    return jsonify({"status": "Bot parado com sucesso."})

@main.route('/status_bot', methods=['GET'])
def status_bot():
    return jsonify({'status': verificador.status_bot()})

@main.route('/remove_keyword/<int:keyword_id>', methods=['POST'])
@login_required
def remove_keyword(keyword_id):
    keyword = Keyword.query.get_or_404(keyword_id)
    if keyword.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Permissão negada'}), 403

    try:
        db.session.delete(keyword)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Palavra-chave removida com sucesso!'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover palavra-chave: {e}")
        return jsonify({'status': 'error', 'message': f'Erro ao remover palavra-chave: {e}'}), 500

# Rota para tornar ou remover administrador
@main.route('/admin/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Você não pode alterar seu próprio status de admin.', 'danger')
        return redirect(url_for('main.admin_dashboard'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Status de administrador de {user.username} atualizado!', 'success')
    return redirect(url_for('main.admin_dashboard'))

# Rota para redefinir a senha do usuário
@main.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = 'defaultpassword'
    user.set_password(new_password)
    db.session.commit()
    flash(f'A senha de {user.username} foi redefinida para: {new_password}', 'success')
    return redirect(url_for('main.admin_dashboard'))

# Rota para editar o e-mail do usuário
@main.route('/admin/edit_email/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_email(user_id):
    user = User.query.get_or_404(user_id)
    new_email = request.form.get('new_email')
    if not new_email or '@' not in new_email:
        flash('E-mail inválido.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    user.email = new_email
    db.session.commit()
    flash(f'O e-mail de {user.username} foi atualizado para {new_email}', 'success')
    return redirect(url_for('main.admin_dashboard'))

# Rota para liberar o acesso do usuário
@main.route('/admin/grant_access/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def grant_access(user_id):
    user = User.query.get_or_404(user_id)
    user.is_subscriber = True
    db.session.commit()
    flash(f'Acesso liberado para o usuário {user.username}!', 'success')
    return redirect(url_for('main.admin_dashboard'))


# Endpoint para receber mensagens via webhook do Telegram
@main.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """
    Webhook do Telegram para capturar o chat ID e associá-lo ao usuário que ainda não tem chat_id,
    apenas quando a mensagem é "/start".
    """
    data = request.get_json()

    if 'message' in data:
        message = data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')

        # Verificar se o comando é "/start"
        if text == "/start":
            logger.info(f"Comando /start recebido do chat ID: {chat_id}")

            # Encontrar o primeiro usuário sem chat_id associado
            user = User.query.filter_by(chat_id=None).first()

            if user:
                # Associar o chat_id ao usuário
                user.chat_id = chat_id
                db.session.commit()

                logger.info(f"Chat ID {chat_id} associado ao usuário {user.username}.")

                # Enviar mensagem de confirmação
                send_telegram_message(chat_id, "Seu chat ID foi associado com sucesso!")
                return jsonify({"status": "Chat ID associado com sucesso"}), 200
            else:
                logger.warning("Nenhum usuário disponível para associação.")
                send_telegram_message(chat_id, "Nenhum usuário disponível para associação.")
                return jsonify({"status": "Nenhum usuário disponível para associação"}), 404

    # Se não for "/start", retorna 200 sem fazer nada
    return jsonify({"status": "Nenhuma ação realizada"}), 200


def send_telegram_message(chat_id, text):
    """
    Função para enviar mensagem ao Telegram.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        logger.error(f"Erro ao enviar mensagem para o chat ID {chat_id}: {response.text}")
    return response
