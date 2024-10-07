from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
from .forms import LoginForm, RegistrationForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota de login, onde o usuário pode se autenticar
    """
    form = LoginForm()  # Usando o formulário centralizado
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Verifica se o usuário existe no banco de dados
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)

            # Redireciona para a página original (se houver) ou para o dashboard
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')

    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """
    Rota de logout, onde o usuário é deslogado da aplicação
    """
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Rota de registro, onde novos usuários podem se cadastrar
    """
    form = RegistrationForm()  # Usando o formulário centralizado
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        phone_number = form.phone_number.data

        # Verifica se o nome de usuário já existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Nome de usuário já existe. Tente outro.', 'danger')
            return redirect(url_for('auth.register'))

        # Certifica-se de que o telefone tem o código do país "55"
        if phone_number and not phone_number.startswith('55'):
            phone_number = '55' + phone_number

        try:
            # Cria um novo usuário com as informações fornecidas
            new_user = User(username=username, phone_number=phone_number)
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
