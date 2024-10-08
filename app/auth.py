from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
from .forms import LoginForm, RegistrationForm

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
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')

    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data  # Certifique-se de coletar o e-mail
        password = form.password.data
        phone_number = form.phone_number.data

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Nome de usuário já existe. Tente outro.', 'danger')
            return redirect(url_for('auth.register'))

        if phone_number and not phone_number.startswith('55'):
            phone_number = '55' + phone_number

        try:
            new_user = User(username=username, email=email, phone_number=phone_number)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao realizar o cadastro: {e}', 'danger')

    return render_template('register.html', form=form)
