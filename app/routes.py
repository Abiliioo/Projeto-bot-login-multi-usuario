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
    """
    Dashboard do usuário, onde ele pode atualizar o chat ID e adicionar palavras-chave
    """
    if request.method == 'POST':
        chat_id = request.form.get('chat_id')
        keywords_input = request.form.get('keyword')

        # Processa as palavras-chave como uma lista separada por vírgulas
        if keywords_input:
            keywords_list = [keyword.strip() for keyword in keywords_input.split(',') if keyword.strip()]
            
            for keyword in keywords_list:
                new_keyword = Keyword(keyword=keyword, user_id=current_user.id)
                db.session.add(new_keyword)

        db.session.commit()
        flash('Suas configurações foram atualizadas com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))

    # Exibe as palavras-chave associadas ao usuário atual
    keywords = Keyword.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', keywords=keywords)


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

@main.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


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
