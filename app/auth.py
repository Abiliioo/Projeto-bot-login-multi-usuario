from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app  # Adiciona current_app
from flask_login import login_user, logout_user, login_required, current_user  # Adiciona current_user
from .models import User
from . import db
from .forms import LoginForm, RegistrationForm
import logging

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')

            # Sanitiza a next_page para evitar redirecionamentos maliciosos
            if next_page and not next_page.startswith('/'):
                next_page = url_for('main.dashboard')

            flash('Login realizado com sucesso!', 'success')
            current_app.logger.info(f"Usuário {username} logou com sucesso.")
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')
            current_app.logger.warning(f"Tentativa de login falha para usuário {username}.")

    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    username = current_user.username  # Obtem o nome de usuário antes de deslogar
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    current_app.logger.info(f"Usuário {username} saiu do sistema.")
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        phone_number = form.phone_number.data

        # Verifica se o nome de usuário já existe
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Nome de usuário já existe. Tente outro.', 'danger')
            return redirect(url_for('auth.register'))
        
        if existing_email:
            flash('Este e-mail já está registrado. Tente outro.', 'danger')
            return redirect(url_for('auth.register'))

        # Validação do número de telefone
        if phone_number and not phone_number.startswith('55'):
            phone_number = '55' + phone_number

        try:
            # Cria um novo usuário
            new_user = User(username=username, email=email, phone_number=phone_number)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            current_app.logger.info(f"Novo usuário cadastrado: {username}.")
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao realizar o cadastro: {e}', 'danger')
            current_app.logger.error(f"Erro ao registrar usuário {username}: {e}")

    return render_template('register.html', form=form)
