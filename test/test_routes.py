import pytest
from flask_login import login_user
from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_database():
    # Adiciona um usuário de teste
    user = User(username='testuser', phone_number='+5511999999999')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

def test_dashboard_access_without_login(client):
    # Testa o acesso ao dashboard sem estar logado
    response = client.get('/dashboard', follow_redirects=True)

    # Verifica se a mensagem de login está presente
    assert 'Por favor, faça login para acessar esta página.' in response.get_data(as_text=True)

    # Verifica se o campo "Nome de Usuário" está presente no formulário de login
    assert 'Nome de Usuário' in response.get_data(as_text=True)

    # Verifique também o código de resposta
    assert response.status_code == 200


def test_dashboard_access_with_login(client, init_database):
    # Testa o acesso ao dashboard com login
    client.post('/auth/login', data=dict(
        username='testuser', password='testpassword'
    ), follow_redirects=True)
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert 'Bem-vindo ao Dashboard' in response.get_data(as_text=True)

