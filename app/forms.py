from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TelField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    confirm_email = StringField('Confirme seu E-mail', validators=[DataRequired(), Email(), EqualTo('email', message="Os e-mails devem coincidir.")])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirme sua Senha', validators=[DataRequired(), EqualTo('password', message="As senhas devem coincidir.")])
    phone_number = TelField('Número de Telefone', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')


# Formulário de Redefinição de Senha
class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('Nova Senha', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirme a Nova Senha', validators=[DataRequired(), EqualTo('new_password', message="As senhas devem coincidir.")])
    submit = SubmitField('Redefinir Senha')


# Formulário de Edição de E-mail
class EditEmailForm(FlaskForm):
    new_email = StringField('Novo E-mail', validators=[DataRequired(), Email()])
    confirm_new_email = StringField('Confirme o Novo E-mail', validators=[DataRequired(), Email(), EqualTo('new_email', message="Os e-mails devem coincidir.")])
    submit = SubmitField('Alterar E-mail')


# Outros formulários podem ser centralizados aqui conforme necessário
