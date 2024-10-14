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

# Definindo o blueprint "main"
main = Blueprint('main', __name__)

# Inicialização global do bot (uma instância global para manter o estado)
verificador = VerificadorDeProjetos()

# Carrega o token do bot a partir do arquivo .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

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
    if not current_user.is_subscriber:
        return jsonify({'status': 'Erro: Apenas assinantes podem iniciar o bot.'}), 403

    total_pages = 10
    keywords = [kw.keyword for kw in current_user.keywords]
    bot_token = TELEGRAM_TOKEN
    chat_id = current_user.chat_id

    if not chat_id:
        return jsonify({'status': 'Erro: Você precisa primeiro interagir com o bot no Telegram para vincular seu Chat ID.'}), 400

    verificador.iniciar_verificacao(total_pages, keywords, bot_token, chat_id)
    return jsonify({'status': 'Bot iniciado com sucesso!'})

@main.route('/stop_bot', methods=['POST'])
@login_required
def stop_bot():
    verificador.parar_verificacao()
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
    Recebe mensagens do Telegram e captura o chat ID do usuário para armazená-lo no banco de dados
    após a confirmação de que o número de telefone corresponde ao cadastrado.
    """
    data = request.get_json()

    if 'message' in data:
        message = data['message']
        chat_id = message['chat']['id']  # Captura o chat ID
        print(f"Mensagem recebida do chat ID: {chat_id}")

        # Quando o comando /start é enviado, solicitamos a confirmação do telefone
        if message.get('text') == '/start':
            # Buscando o usuário que está atualmente logado na plataforma, para confirmar com o Telegram
            # Aqui devemos obter o telefone diretamente do banco de dados (ex: usuário atual).
            user = User.query.filter_by(phone_number=current_user.phone_number).first() 

            if user:
                bot_token = os.getenv('TELEGRAM_TOKEN')
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': f"O número de telefone cadastrado na plataforma é {user.phone_number}. Este é o seu telefone?",
                    'reply_markup': {
                        'keyboard': [['Sim', 'Não']],
                        'one_time_keyboard': True
                    }
                }
                requests.post(url, json=payload)
                return jsonify({'status': 'success', 'message': 'Solicitação de confirmação de telefone enviada.'}), 200

        # Se o usuário confirmar que o telefone está correto
        if message.get('text') == 'Sim':
            # Agora, confirmamos se o chat_id já está vazio para evitar duplicações
            user = User.query.filter_by(phone_number=current_user.phone_number, chat_id=None).first()

            if user:
                user.chat_id = chat_id  # Atribuir o chat ID ao usuário
                db.session.commit()
                return jsonify({'status': 'success', 'message': f'Chat ID {chat_id} associado ao telefone {user.phone_number}.'}), 200

        # Se o usuário disser que o número de telefone não está correto
        if message.get('text') == 'Não':
            return jsonify({'status': 'error', 'message': 'Por favor, atualize o número de telefone na plataforma.'}), 400

    return jsonify({'status': 'error', 'message': 'Mensagem inválida.'}), 400
