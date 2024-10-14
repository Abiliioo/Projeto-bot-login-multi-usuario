from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TelField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Regexp

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(message="Por favor, insira um nome de usuário.")])
    email = StringField('E-mail', validators=[DataRequired(message="Por favor, insira um e-mail."), Email(message="Por favor, insira um e-mail válido.")])
    confirm_email = StringField('Confirme seu E-mail', validators=[DataRequired(), Email(), EqualTo('email', message="Os e-mails devem coincidir.")])
    password = PasswordField('Senha', validators=[DataRequired(message="Por favor, insira uma senha.")])
    confirm_password = PasswordField('Confirme sua Senha', validators=[DataRequired(), EqualTo('password', message="As senhas devem coincidir.")])
    phone_number = TelField('Número de Telefone', validators=[
        DataRequired(message="Por favor, insira um número de telefone."),
        Regexp(r'^55\d{10,11}$', message="Por favor, insira um número de telefone válido no formato brasileiro (ex: 5511998765432).")
    ])
    submit = SubmitField('Cadastrar')

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(message="Por favor, insira o nome de usuário.")])
    password = PasswordField('Senha', validators=[DataRequired(message="Por favor, insira a senha.")])
    submit = SubmitField('Entrar')

# Formulário de Redefinição de Senha
class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('Nova Senha', validators=[DataRequired(message="Por favor, insira a nova senha.")])
    confirm_new_password = PasswordField('Confirme a Nova Senha', validators=[DataRequired(), EqualTo('new_password', message="As senhas devem coincidir.")])
    submit = SubmitField('Redefinir Senha')

# Formulário de Edição de E-mail
class EditEmailForm(FlaskForm):
    new_email = StringField('Novo E-mail', validators=[DataRequired(message="Por favor, insira um novo e-mail."), Email(message="Por favor, insira um e-mail válido.")])
    confirm_new_email = StringField('Confirme o Novo E-mail', validators=[DataRequired(), Email(), EqualTo('new_email', message="Os e-mails devem coincidir.")])
    submit = SubmitField('Alterar E-mail')
