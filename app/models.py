from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash  # Para lidar com as senhas
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Campo para definir se o usuário é administrador
    chat_id = db.Column(db.String(50), nullable=True)
    keywords = db.relationship('Keyword', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_phone_number(self, phone_number):
        self.phone_number = phone_number

class Keyword(db.Model):
    """Tabela para armazenar as palavras-chave associadas aos usuários"""
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(50), nullable=False)
    
    # Chave estrangeira referenciando o usuário
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
