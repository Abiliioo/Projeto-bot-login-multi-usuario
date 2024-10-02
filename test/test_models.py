import pytest
from app import create_app, db
from app.models import User, Keyword

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def init_database(app):  # Adiciona o 'app' como argumento para garantir que o contexto esteja ativo
    # Adiciona um usuário de teste dentro do contexto da aplicação
    with app.app_context():
        user = User(username='testuser', phone_number='+5511999999999')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

def test_create_user(init_database):
    # Testa a criação de um usuário
    user = User.query.filter_by(username='testuser').first()
    assert user is not None
    assert user.check_password('testpassword')

def test_add_keyword(init_database):
    # Testa a adição de uma palavra-chave ao usuário
    user = User.query.filter_by(username='testuser').first()
    keyword = Keyword(keyword='python', user_id=user.id)
    db.session.add(keyword)
    db.session.commit()
    
    keywords = Keyword.query.filter_by(user_id=user.id).all()
    assert len(keywords) == 1
    assert keywords[0].keyword == 'python'
