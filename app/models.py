from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from datetime import datetime, timezone, timedelta

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(512), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_subscriber = db.Column(db.Boolean, default=False)  # Campo para status de assinante
    chat_id = db.Column(db.String(50), nullable=True)
    keywords = db.relationship('Keyword', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Gera o hash da senha."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha informada corresponde ao hash armazenado."""
        return check_password_hash(self.password_hash, password)

    def set_phone_number(self, phone_number):
        """Define ou atualiza o número de telefone, adicionando o código do país '55' se necessário."""
        if phone_number and not phone_number.startswith('55'):
            phone_number = '55' + phone_number
        self.phone_number = phone_number

    def __repr__(self):
        return f'<User {self.username}>'


class Keyword(db.Model):
    __tablename__ = 'keywords'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Keyword {self.keyword}>'

    @staticmethod
    def clean_keyword(keyword):
        """Método para limpar e formatar a palavra-chave antes de armazenar."""
        return keyword.strip().lower()

    def save(self):
        """Salva a palavra-chave no banco de dados."""
        self.keyword = Keyword.clean_keyword(self.keyword)
        db.session.add(self)
        db.session.commit()


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Garantindo que o fuso horário seja UTC
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Project {self.title}>'

    @staticmethod
    def delete_old_projects():
        """
        Exclui projetos que foram adicionados há mais de 12 horas de uma vez.
        """
        threshold_time = datetime.now(timezone.utc) - timedelta(hours=12)
        Project.query.filter(Project.date_added < threshold_time).delete()
        db.session.commit()

    def save(self):
        """Salva o projeto no banco de dados."""
        db.session.add(self)
        db.session.commit()
