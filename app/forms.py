from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TelField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    confirm_email = StringField('Confirme seu E-mail', validators=[DataRequired(), Email(), EqualTo('email', message="Os e-mails devem coincidir.")])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirme sua Senha', validators=[DataRequired(), EqualTo('password', message="As senhas devem coincidir.")])
    phone_number = TelField('Número de Telefone', validators=[DataRequired()])
    is_admin = BooleanField('Administrador')  # Apenas para teste, remova se não for necessário
    submit = SubmitField('Cadastrar')

    # Validação personalizada para o número de telefone
    def validate_phone_number(self, field):
        if not field.data.startswith('55'):
            field.data = '55' + field.data
