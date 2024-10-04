import os  # Importando o módulo os para ler o arquivo .env
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user
from .models import Keyword, User
from . import db
from .forms import RegistrationForm
from flask import Blueprint
from .decorators import admin_required
from .bot import VerificadorDeProjetos  # Importando a classe do bot

# Definindo o blueprint "main"
main = Blueprint('main', __name__)

# Inicialização do bot
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
    # Verifica se o usuário é admin e redireciona para o painel correto
    if current_user.is_admin:
        return redirect(url_for('main.admin_dashboard'))

    # Lógica para salvar palavras-chave
    if request.method == 'POST':
        # Adicionar prints para depuração
        print("Método POST detectado")
        keywords_input = request.form.get('keyword')
        print(f"Palavras recebidas: {keywords_input}")

        if keywords_input:
            keywords_list = [keyword.strip() for keyword in keywords_input.split(',') if keyword.strip()]
            print(f"Palavras processadas: {keywords_list}")

            for keyword in keywords_list:
                existing_keyword = Keyword.query.filter_by(keyword=keyword, user_id=current_user.id).first()
                if not existing_keyword:
                    new_keyword = Keyword(keyword=keyword, user_id=current_user.id)
                    db.session.add(new_keyword)

        try:
            db.session.commit()
            print("Palavras-chave salvas com sucesso!")
            flash('Palavras-chave salvas com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar palavras-chave: {e}")
            flash('Erro ao salvar suas palavras-chave.', 'danger')

        return redirect(url_for('main.dashboard'))

    # Exibe as palavras-chave associadas ao usuário atual
    keywords = Keyword.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', keywords=keywords)



@main.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard():
    """
    Painel administrativo para gerenciar usuários e palavras-chave.
    """
    # Processa o POST das palavras-chave
    if request.method == 'POST':
        keywords_input = request.form.get('keyword')
        print(f"Palavras recebidas no admin: {keywords_input}")

        if keywords_input:
            keywords_list = [keyword.strip() for keyword in keywords_input.split(',') if keyword.strip()]
            print(f"Palavras processadas no admin: {keywords_list}")

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
            print(f"Erro ao salvar as palavras-chave no admin: {e}")
            flash(f'Erro ao salvar palavras-chave: {e}', 'danger')

    # Pega todos os usuários e palavras-chave para o admin gerenciar
    users = User.query.all()
    keywords = Keyword.query.filter_by(user_id=current_user.id).all()  # Adiciona essa linha

    return render_template('admin.html', users=users, keywords=keywords)


@main.route('/cadastro', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        phone_number = form.phone_number.data
        is_admin = form.is_admin.data  # Coleta o status de administrador

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Nome de usuário já existe. Tente outro.', 'danger')
            return redirect(url_for('main.register'))

        try:
            # Certifica-se de que o telefone tem o código do país "55"
            if phone_number and not phone_number.startswith('55'):
                phone_number = '55' + phone_number

            new_user = User(username=username, email=email, phone_number=phone_number, is_admin=is_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao realizar o cadastro: {e}', 'danger')

    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota de login do usuário
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verifica se o usuário existe
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')

    return render_template('login.html')


# Controle do bot: Iniciar e parar bot
@main.route('/start_bot', methods=['POST'])
@login_required
def start_bot():
    """
    Inicia o bot de verificação de projetos
    """
    # Obtendo palavras-chave do usuário
    keywords = [kw.keyword for kw in Keyword.query.filter_by(user_id=current_user.id).all()]
    if current_user.chat_id and TELEGRAM_TOKEN:
        verificador.iniciar_verificacao(10, keywords, TELEGRAM_TOKEN, current_user.chat_id)
        return jsonify({"status": "Bot iniciado com sucesso."})
    else:
        return jsonify({"status": "Chat ID ou token do bot não encontrado. Inicie a conversa com o bot ou verifique o token."})

@main.route('/stop_bot', methods=['POST'])
@login_required
def stop_bot():
    """
    Para o bot de verificação de projetos
    """
    verificador.parar_verificacao()
    return jsonify({"status": "Bot parado com sucesso."})

# Rota para remover uma palavra-chave
@main.route('/remove_keyword/<int:keyword_id>', methods=['POST'])
@login_required
def remove_keyword(keyword_id):
    keyword = Keyword.query.get_or_404(keyword_id)
    if keyword.user_id != current_user.id:
        flash('Você não tem permissão para remover esta palavra-chave.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(keyword)
    db.session.commit()
    flash('Palavra-chave removida com sucesso!', 'success')
    return redirect(url_for('main.dashboard'))

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
    new_password = 'defaultpassword'  # Defina uma senha padrão ou gere aleatoriamente
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
    user.is_subscriber = True  # Aqui você pode marcar o usuário como assinante
    db.session.commit()
    flash(f'Acesso liberado para o usuário {user.username}!', 'success')
    return redirect(url_for('main.admin_dashboard'))
