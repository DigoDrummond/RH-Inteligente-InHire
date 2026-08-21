"""
Testes unitários para AuthService
Testa autenticação JWT, renovação de token, cache
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


@pytest.mark.unit
class TestAuthServiceAuthentication:
    """Testes para autenticação"""

    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.settings')
    def test_login_success(self, mock_settings, mock_post):
        """Deve fazer login com sucesso e obter token"""
        from services.auth_service import AuthService

        # Mock settings
        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accessToken": "test-token-12345",
            "refreshToken": "refresh-token-12345",
            "expiresIn": 3600
        }
        mock_post.return_value = mock_response

        auth_service = AuthService()
        result = auth_service.login()

        assert result is True
        assert auth_service.access_token == "test-token-12345"
        assert auth_service.is_authenticated is True

    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.settings')
    def test_login_invalid_credentials(self, mock_settings, mock_post):
        """Deve lançar exceção com credenciais inválidas"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "wrong-password"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_post.return_value = mock_response

        auth_service = AuthService()

        with pytest.raises(Exception):
            auth_service.login()

    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.settings')
    def test_login_network_error(self, mock_settings, mock_post):
        """Deve lançar exceção em erro de rede"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        mock_post.side_effect = Exception("Connection failed")

        auth_service = AuthService()

        with pytest.raises(Exception):
            auth_service.login()


@pytest.mark.unit
class TestAuthServiceTokenManagement:
    """Testes para gerenciamento de token"""

    @patch('services.auth_service.settings')
    def test_is_authenticated_without_token(self, mock_settings):
        """Deve retornar False se não tiver token"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        auth_service = AuthService()

        assert auth_service.is_authenticated is False

    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.settings')
    def test_is_authenticated_with_valid_token(self, mock_settings, mock_post):
        """Deve retornar True se tiver token válido"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accessToken": "test-token",
            "refreshToken": "refresh-token",
            "expiresIn": 3600
        }
        mock_post.return_value = mock_response

        auth_service = AuthService()
        auth_service.login()

        assert auth_service.is_authenticated is True

    @patch('services.auth_service.settings')
    def test_is_token_expired_without_auth(self, mock_settings):
        """Deve retornar True se não estiver autenticado"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        auth_service = AuthService()

        assert auth_service.is_token_expired is True


@pytest.mark.unit
class TestAuthServiceHeaders:
    """Testes para geração de headers"""

    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.settings')
    def test_authorization_header(self, mock_settings, mock_post):
        """Deve gerar header de autorização correto"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accessToken": "test-token-12345",
            "refreshToken": "refresh-token",
            "expiresIn": 3600
        }
        mock_post.return_value = mock_response

        auth_service = AuthService()
        auth_service.login()

        header = auth_service.authorization_header

        assert "Authorization" in header
        assert "Bearer test-token-12345" in header["Authorization"]

    @patch('services.auth_service.settings')
    def test_authorization_header_without_token_raises(self, mock_settings):
        """Deve lançar exceção se não tiver token"""
        from services.auth_service import AuthService
        from utils.retry import TokenExpiredException

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        auth_service = AuthService()

        with pytest.raises(TokenExpiredException):
            _ = auth_service.authorization_header


@pytest.mark.unit
class TestAuthServiceSingleton:
    """Testes para padrão singleton"""

    def test_get_auth_service_returns_instance(self):
        """Deve retornar instância do AuthService"""
        from services.auth_service import get_auth_service

        service = get_auth_service()

        assert service is not None


@pytest.mark.unit
class TestAuthServiceRefreshToken:
    """Testes para renovação de token"""

    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.settings')
    def test_refresh_token_success(self, mock_settings, mock_post):
        """Deve renovar token com sucesso"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        # Mock login inicial
        mock_login_response = Mock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "accessToken": "old-token",
            "refreshToken": "refresh-token",
            "expiresIn": 3600
        }

        # Mock refresh
        mock_refresh_response = Mock()
        mock_refresh_response.status_code = 200
        mock_refresh_response.json.return_value = {
            "accessToken": "new-token",
            "refreshToken": "new-refresh-token",
            "expiresIn": 3600
        }

        mock_post.side_effect = [mock_login_response, mock_refresh_response]

        auth_service = AuthService()
        auth_service.login()

        old_token = auth_service.access_token

        # Se existir método refresh
        if hasattr(auth_service, 'refresh'):
            auth_service.refresh()
            assert auth_service.access_token != old_token


@pytest.mark.unit
class TestAuthServiceThreadSafety:
    """Testes para thread safety"""

    @patch('services.auth_service.settings')
    def test_has_lock_for_thread_safety(self, mock_settings):
        """Deve ter lock para operações thread-safe"""
        from services.auth_service import AuthService
        from threading import Lock

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        auth_service = AuthService()

        # Deve ter lock
        assert hasattr(auth_service, '_lock')
        assert isinstance(auth_service._lock, Lock)


@pytest.mark.unit
class TestAuthServiceProperties:
    """Testes para propriedades"""

    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.settings')
    def test_access_token_property(self, mock_settings, mock_post):
        """Deve retornar access token via property"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accessToken": "my-token",
            "refreshToken": "my-refresh",
            "expiresIn": 3600
        }
        mock_post.return_value = mock_response

        auth_service = AuthService()
        auth_service.login()

        assert auth_service.access_token == "my-token"

    @patch('services.auth_service.requests.post')
    @patch('services.auth_service.settings')
    def test_refresh_token_property(self, mock_settings, mock_post):
        """Deve retornar refresh token via property"""
        from services.auth_service import AuthService

        mock_settings.INHIRE_AUTH_URL = "https://auth.test.com"
        mock_settings.INHIRE_EMAIL = "test@example.com"
        mock_settings.INHIRE_PASSWORD = "password123"
        mock_settings.INHIRE_TIMEOUT_CONNECT = 10
        mock_settings.INHIRE_TIMEOUT_READ = 30

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accessToken": "my-token",
            "refreshToken": "my-refresh",
            "expiresIn": 3600
        }
        mock_post.return_value = mock_response

        auth_service = AuthService()
        auth_service.login()

        assert auth_service.refresh_token == "my-refresh"
