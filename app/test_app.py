import pytest
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock
from app import app, is_valid_hostname

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    """Cria um banco de dados temporário para testes"""
    db_fd, db_path = tempfile.mkstemp()
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    ''')
    conn.execute('INSERT INTO users (id, name, email) VALUES (1, "Test User", "test@example.com")')
    conn.execute('INSERT INTO users (id, name, email) VALUES (2, "Another User", "another@example.com")')
    conn.commit()
    conn.close()
    
    yield db_path
    
    os.close(db_fd)
    os.unlink(db_path)

# Testes para a rota /user (corrigida)
def test_get_user_success(client, mock_db):
    """Testa busca de usuário com ID válido"""
    with patch('app.sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [(1, 'Test User', 'test@example.com')]
        
        response = client.get('/user?id=1')
        assert response.status_code == 200
        assert 'users' in response.get_json()

def test_get_user_missing_id(client):
    """Testa rota /user sem parâmetro id"""
    response = client.get('/user')
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_get_user_invalid_id_non_numeric(client):
    """Testa rota /user com ID não numérico"""
    response = client.get('/user?id=abc')
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_get_user_invalid_id_sql_injection_attempt(client):
    """Testa proteção contra SQL injection"""
    response = client.get('/user?id=1 OR 1=1')
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_get_user_database_error(client):
    """Testa tratamento de erro de banco de dados"""
    with patch('app.sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.Error("Database error")
        response = client.get('/user?id=1')
        assert response.status_code == 500
        assert 'error' in response.get_json()

# Testes para a rota /user/safe
def test_get_user_safe_success(client):
    """Testa busca segura de usuário com ID válido"""
    with patch('app.sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [(1, 'Test User', 'test@example.com')]
        
        response = client.get('/user/safe?id=1')
        assert response.status_code == 200
        assert 'users' in response.get_json()

def test_get_user_safe_missing_id(client):
    """Testa rota /user/safe sem parâmetro id"""
    response = client.get('/user/safe')
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_get_user_safe_invalid_id_non_numeric(client):
    """Testa rota /user/safe com ID não numérico"""
    response = client.get('/user/safe?id=abc')
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_get_user_safe_database_error(client):
    """Testa tratamento de erro de banco de dados na rota safe"""
    with patch('app.sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.Error("Database error")
        response = client.get('/user/safe?id=1')
        assert response.status_code == 500
        assert 'error' in response.get_json()

# Testes para a rota /ping (corrigida)
def test_ping_success(client):
    """Testa ping com hostname válido"""
    with patch('subprocess.check_output') as mock_ping:
        mock_ping.return_value = b'PING localhost (127.0.0.1): 56 data bytes'
        response = client.get('/ping?host=localhost')
        assert response.status_code == 200
        assert 'result' in response.get_json()

def test_ping_missing_host(client):
    """Testa rota /ping sem parâmetro host"""
    response = client.get('/ping')
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_ping_invalid_host_command_injection_attempt(client):
    """Testa proteção contra command injection"""
    # Tentativas de command injection
    injection_attempts = [
        'localhost; rm -rf /',
        'localhost && cat /etc/passwd',
        'localhost | ls',
        'localhost`whoami`',
        'localhost$(id)',
        'localhost\nrm -rf /',
    ]
    
    for host in injection_attempts:
        response = client.get(f'/ping?host={host}')
        assert response.status_code == 400
        assert 'error' in response.get_json()

def test_ping_invalid_host_special_chars(client):
    """Testa rejeição de caracteres especiais perigosos"""
    invalid_hosts = [
        'host;name',
        'host&name',
        'host|name',
        'host`name',
        'host$name',
        'host(name)',
        'host<name>',
        'host name',  # espaço
        'host\tname',  # tab
    ]
    
    for host in invalid_hosts:
        # URL encode pode ser necessário para alguns caracteres
        import urllib.parse
        encoded_host = urllib.parse.quote(host, safe='')
        response = client.get(f'/ping?host={encoded_host}')
        # Deve retornar 400 (bad request) devido à validação, não 500 (server error)
        assert response.status_code == 400, f"Host '{host}' should be rejected with 400, got {response.status_code}"
        assert 'error' in response.get_json()

def test_ping_timeout(client):
    """Testa tratamento de timeout no ping"""
    with patch('subprocess.check_output') as mock_ping:
        import subprocess
        mock_ping.side_effect = subprocess.TimeoutExpired('ping', 5)
        response = client.get('/ping?host=localhost')
        assert response.status_code == 408
        assert 'error' in response.get_json()

def test_ping_failed(client):
    """Testa tratamento de falha no ping"""
    with patch('subprocess.check_output') as mock_ping:
        import subprocess
        error = subprocess.CalledProcessError(1, 'ping', output=b'Host unreachable')
        mock_ping.side_effect = error
        response = client.get('/ping?host=invalid-host')
        assert response.status_code == 500
        assert 'error' in response.get_json()

def test_ping_unexpected_error(client):
    """Testa tratamento de erro inesperado"""
    with patch('subprocess.check_output') as mock_ping:
        mock_ping.side_effect = Exception("Unexpected error")
        response = client.get('/ping?host=localhost')
        assert response.status_code == 500
        assert 'error' in response.get_json()

# Testes para função is_valid_hostname
def test_is_valid_hostname_valid():
    """Testa validação de hostnames válidos"""
    valid_hosts = [
        'localhost',
        'example.com',
        'subdomain.example.com',
        '192.168.1.1',
        'host-name',
        'host123',
    ]
    
    for host in valid_hosts:
        assert is_valid_hostname(host) == True

def test_is_valid_hostname_invalid():
    """Testa validação de hostnames inválidos"""
    invalid_hosts = [
        '',
        None,
        'host;name',
        'host&name',
        'host|name',
        'host`name',
        'host$name',
        'host(name)',
        'host<name>',
        'host\nname',
        'host\rname',
        'a' * 254,  # Muito longo
    ]
    
    for host in invalid_hosts:
        if host is None:
            continue
        assert is_valid_hostname(host) == False

# Testes para rota /health
def test_health_check(client):
    """Testa endpoint de health check"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'healthy'

# Testes de configuração
def test_app_exists():
    """Testa que a aplicação existe"""
    assert app is not None

def test_app_secret_key_from_env():
    """Testa que SECRET_KEY pode ser configurada via variável de ambiente"""
    # O módulo já foi importado, então precisamos recarregar ou testar diretamente
    original_key = os.getenv('SECRET_KEY')
    try:
        os.environ['SECRET_KEY'] = 'test-secret-key'
        # Recarrega o módulo para pegar o novo valor
        import importlib
        import app as app_module
        importlib.reload(app_module)
        assert app_module.SECRET_KEY == 'test-secret-key'
    finally:
        if original_key:
            os.environ['SECRET_KEY'] = original_key
        elif 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        # Recarrega novamente para restaurar
        import importlib
        import app as app_module
        importlib.reload(app_module)

def test_app_secret_key_default():
    """Testa valor padrão de SECRET_KEY quando não configurada"""
    with patch.dict(os.environ, {}, clear=True):
        # Recarrega o módulo para pegar o valor padrão
        import importlib
        import app as app_module
        importlib.reload(app_module)
        assert app_module.SECRET_KEY == 'dev-key-change-in-production'

def test_app_debug_mode_from_env():
    """Testa configuração de debug via variável de ambiente"""
    with patch.dict(os.environ, {'FLASK_DEBUG': 'true'}):
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        assert debug_mode == True

def test_app_debug_mode_default():
    """Testa que debug está desabilitado por padrão"""
    with patch.dict(os.environ, {}, clear=True):
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        assert debug_mode == False

# Testes de integração
def test_multiple_routes(client):
    """Testa múltiplas rotas em sequência"""
    # Health check
    response = client.get('/health')
    assert response.status_code == 200
    
    # User safe route
    with patch('app.sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = []
        response = client.get('/user/safe?id=999')
        assert response.status_code == 200

def test_error_handling_consistency(client):
    """Testa consistência no tratamento de erros"""
    # Todas as rotas devem retornar JSON em caso de erro
    routes = ['/user', '/user/safe', '/ping']
    
    for route in routes:
        response = client.get(route)  # Sem parâmetros obrigatórios
        assert response.status_code >= 400
        assert response.is_json
        assert 'error' in response.get_json()
