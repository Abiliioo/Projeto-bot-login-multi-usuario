import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    # Cria a aplicação Flask com o ambiente de teste
    app = create_app('testing')
    with app.app_context():
        db.create_all()  # Cria todas as tabelas
        yield app
        db.session.remove()
        db.drop_all()  # Limpa o banco de dados após o teste

@pytest.fixture
def client(app):
    return app.test_client()  # Cria um cliente de teste

@pytest.fixture
def init_database():
    # Adiciona um usuário para teste de login
    user = User(username='testuser', phone_number='+5511999999999')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

def test_login(client, init_database):
    # Testa o login com as credenciais corretas
    response = client.post('/auth/login', data=dict(
        username='testuser', password='testpassword'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Login realizado com sucesso!' in response.data  # Verifica se a mensagem de sucesso está presente
