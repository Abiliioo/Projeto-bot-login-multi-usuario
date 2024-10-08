import os  # Importando o módulo os para ler o arquivo .env
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .models import Keyword, User
from . import db
from flask import Blueprint
from .decorators import admin_required
from .bot import VerificadorDeProjetos  # Importando a classe do bot

# Definindo o blueprint "main"
main = Blueprint('main', __name__)

# Inicialização global do bot (uma instância global para manter o estado)
verificador = VerificadorDeProjetos()

# Carrega o token do bot a partir do arquivo .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

@main.route('/')
def home():
    """
    Página inicial (landing page)
    """
    return render_template('index.html')

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """
    Exibe o painel de controle para usuários comuns.
    Admins podem salvar palavras-chave e depois são redirecionados para o painel administrativo.
    """
    if request.method == 'POST':
        keywords_input = request.form.get('keyword')
        if keywords_input:
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

    if current_user.is_admin:
        return redirect(url_for('main.admin_dashboard'))

    keywords = Keyword.query.filter_by(user_id=current_user.id).all()

    return render_template('dashboard.html', keywords=keywords)

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

    db.session.delete(keyword)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Palavra-chave removida com sucesso!'})

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
    if not new_email:
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
