"""
Serviço de Autenticação para API Inhire
Gerencia tokens JWT (access e refresh tokens)
"""
import requests
from typing import Optional, Dict
from datetime import datetime, timedelta
from threading import Lock
from interfaces.i_auth_service import IAuthService
from config import settings, get_default_headers, InhireEndpoints
from models.api_schemas import LoginRequest, LoginResponse, RefreshTokenRequest
from utils.logger import get_logger
from utils.retry import retry_with_backoff, TokenExpiredException


class AuthService(IAuthService):
    """
    Gerenciador de autenticação JWT para API Inhire

    Responsabilidades:
    - Login inicial com credenciais
    - Renovação automática de token
    - Armazenamento seguro de tokens
    - Verificação de validade de token
    """

    def __init__(self):
        """Inicializa o serviço de autenticação"""
        self.logger = get_logger(__name__)

        # URLs de autenticação
        self.auth_base_url = settings.INHIRE_AUTH_URL.rstrip('/')

        # Credenciais
        self.email = settings.INHIRE_EMAIL
        self.password = settings.INHIRE_PASSWORD

        # Tokens
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._token_type: str = "Bearer"

        # Lock para operações thread-safe
        self._lock = Lock()

        # Timeout para requisições
        self.timeout = (
            settings.INHIRE_TIMEOUT_CONNECT,
            settings.INHIRE_TIMEOUT_READ
        )

    # ========================================
    # Propriedades
    # ========================================

    @property
    def access_token(self) -> Optional[str]:
        """Retorna o access token atual"""
        return self._access_token

    @property
    def refresh_token(self) -> Optional[str]:
        """Retorna o refresh token atual"""
        return self._refresh_token

    @property
    def is_authenticated(self) -> bool:
        """Verifica se está autenticado com token válido"""
        if not self._access_token:
            return False

        # Se temos informação de expiração, verificar
        if self._token_expiry:
            # Considerar token inválido se vai expirar em menos de 5 minutos
            return datetime.utcnow() + timedelta(minutes=5) < self._token_expiry

        # Se não temos informação de expiração, assumir que está válido
        return True

    @property
    def is_token_expired(self) -> bool:
        """Verifica se o token está expirado"""
        return not self.is_authenticated

    def is_token_valid(self) -> bool:
        """Verifica se token ainda é válido (implementação da interface)"""
        return self.is_authenticated

    @property
    def authorization_header(self) -> Dict[str, str]:
        """Retorna header de autorização"""
        if not self._access_token:
            raise TokenExpiredException("Token não disponível")

        return {"Authorization": f"{self._token_type} {self._access_token}"}

    # ========================================
    # Métodos de Autenticação
    # ========================================

    @retry_with_backoff(max_attempts=3)
    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Realiza login na API Inhire

        Args:
            email: Email de login (opcional, usa config se não fornecido)
            password: Senha de login (opcional, usa config se não fornecido)

        Returns:
            True se login bem-sucedido, False caso contrário

        Raises:
            RequestException: Em caso de erro de rede
        """
        with self._lock:
            email = email or self.email
            password = password or self.password

            if not email or not password:
                self.logger.error("Credenciais não fornecidas")
                return False

            try:
                self.logger.info(f"Realizando login para {email}...")

                # Preparar requisição
                url = f"{self.auth_base_url}{InhireEndpoints.LOGIN}"
                headers = get_default_headers()

                login_data = LoginRequest(email=email, password=password)
                payload = login_data.model_dump()

                # Realizar requisição
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    login_response = LoginResponse(**data)

                    # Armazenar tokens
                    self._access_token = login_response.accessToken
                    self._refresh_token = login_response.refreshToken
                    self._token_type = login_response.tokenType or "Bearer"

                    # Calcular expiração (se fornecida)
                    if login_response.expiresIn:
                        self._token_expiry = datetime.utcnow() + timedelta(
                            seconds=login_response.expiresIn
                        )
                    else:
                        # Assumir 1 hora se não fornecido
                        self._token_expiry = datetime.utcnow() + timedelta(hours=1)

                    self.logger.info("Login realizado com sucesso")
                    self.logger.debug(f"Token expira em: {self._token_expiry}")

                    return True

                else:
                    self.logger.error(
                        f"Falha no login: HTTP {response.status_code} - {response.text}"
                    )
                    return False

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Erro de rede durante login: {str(e)}")
                raise

            except Exception as e:
                self.logger.error(f"Erro inesperado durante login: {str(e)}", exc_info=True)
                return False

    @retry_with_backoff(max_attempts=3)
    def refresh(self) -> bool:
        """
        Renova o access token usando refresh token

        Returns:
            True se renovação bem-sucedida, False caso contrário

        Raises:
            TokenExpiredException: Se não há refresh token disponível
            RequestException: Em caso de erro de rede
        """
        with self._lock:
            if not self._refresh_token:
                raise TokenExpiredException("Refresh token não disponível")

            try:
                self.logger.info("Renovando access token...")

                # Preparar requisição
                url = f"{self.auth_base_url}{InhireEndpoints.REFRESH}"
                headers = get_default_headers()

                refresh_data = RefreshTokenRequest(refreshToken=self._refresh_token)
                payload = refresh_data.model_dump()

                # Realizar requisição
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    login_response = LoginResponse(**data)

                    # Atualizar tokens
                    self._access_token = login_response.accessToken

                    # Atualizar refresh token se fornecido
                    if login_response.refreshToken:
                        self._refresh_token = login_response.refreshToken

                    # Atualizar expiração
                    if login_response.expiresIn:
                        self._token_expiry = datetime.utcnow() + timedelta(
                            seconds=login_response.expiresIn
                        )
                    else:
                        self._token_expiry = datetime.utcnow() + timedelta(hours=1)

                    self.logger.info("Token renovado com sucesso")
                    return True

                else:
                    self.logger.error(
                        f"Falha na renovação do token: HTTP {response.status_code} - {response.text}"
                    )
                    return False

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Erro de rede durante renovação: {str(e)}")
                raise

            except Exception as e:
                self.logger.error(f"Erro inesperado durante renovação: {str(e)}", exc_info=True)
                return False

    def authenticate(self) -> bool:
        """
        Autentica na API (login ou refresh)

        Estratégia:
        1. Se não tem token, fazer login
        2. Se tem token expirado e refresh token, tentar refresh
        3. Se refresh falhar, fazer login

        Returns:
            True se autenticado com sucesso, False caso contrário
        """
        # Se já está autenticado, não precisa fazer nada
        if self.is_authenticated:
            self.logger.debug("Já autenticado com token válido")
            return True

        # Se tem refresh token, tentar renovar
        if self._refresh_token:
            try:
                self.logger.info("Tentando renovar token...")
                if self.refresh():
                    return True
                else:
                    self.logger.warning("Renovação falhou, tentando login completo")
            except Exception as e:
                self.logger.warning(f"Erro durante renovação: {str(e)}")

        # Fazer login completo
        self.logger.info("Realizando login completo...")
        return self.login()

    def logout(self):
        """Limpa tokens (logout local)"""
        with self._lock:
            self.logger.info("Realizando logout...")
            self._access_token = None
            self._refresh_token = None
            self._token_expiry = None

    # ========================================
    # Métodos Auxiliares
    # ========================================

    def ensure_authenticated(self):
        """
        Garante que está autenticado, renovando token se necessário

        Raises:
            TokenExpiredException: Se não conseguir autenticar
        """
        if not self.is_authenticated:
            self.logger.warning("Token expirado ou inválido, tentando renovar...")

            if not self.authenticate():
                raise TokenExpiredException("Falha ao autenticar com API Inhire")

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Retorna headers completos com autenticação

        Returns:
            Dict com headers incluindo Authorization

        Raises:
            TokenExpiredException: Se não está autenticado
        """
        self.ensure_authenticated()

        headers = get_default_headers(token=self._access_token)
        return headers

    def test_connection(self) -> bool:
        """
        Testa conexão com a API de autenticação

        Returns:
            True se consegue conectar, False caso contrário
        """
        try:
            response = requests.get(
                self.auth_base_url,
                timeout=self.timeout
            )
            return response.status_code < 500
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão: {str(e)}")
            return False


# ========================================
# Instância Global (Singleton)
# ========================================

_auth_service_instance: Optional[AuthService] = None
_instance_lock = Lock()


def get_auth_service() -> AuthService:
    """
    Retorna instância singleton do AuthService

    Returns:
        Instância única de AuthService
    """
    global _auth_service_instance

    if _auth_service_instance is None:
        with _instance_lock:
            if _auth_service_instance is None:
                _auth_service_instance = AuthService()

    return _auth_service_instance


if __name__ == "__main__":
    """Testa o serviço de autenticação"""

    # Configurar logging para teste
    import logging
    logging.basicConfig(level=logging.DEBUG)

    # Criar serviço
    auth_service = get_auth_service()

    print("=== Teste de Autenticação Inhire ===\n")

    # Teste 1: Verificar conexão
    print("1. Testando conexão com API...")
    if auth_service.test_connection():
        print("   ✓ Conexão OK\n")
    else:
        print("   ✗ Falha na conexão\n")

    # Teste 2: Login
    print("2. Realizando login...")
    if auth_service.login():
        print("   ✓ Login bem-sucedido")
        print(f"   Access Token: {auth_service.access_token[:50]}...")
        print(f"   Expira em: {auth_service._token_expiry}\n")
    else:
        print("   ✗ Falha no login\n")

    # Teste 3: Verificar autenticação
    print("3. Verificando autenticação...")
    if auth_service.is_authenticated:
        print("   ✓ Autenticado\n")
    else:
        print("   ✗ Não autenticado\n")

    # Teste 4: Obter headers
    print("4. Obtendo headers de autenticação...")
    try:
        headers = auth_service.get_auth_headers()
        print("   ✓ Headers obtidos:")
        for key, value in headers.items():
            if key == "Authorization":
                print(f"     {key}: {value[:30]}...")
            else:
                print(f"     {key}: {value}")
        print()
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")

    # Teste 5: Renovar token (simular)
    print("5. Testando renovação de token...")
    if auth_service._refresh_token:
        if auth_service.refresh():
            print("   ✓ Token renovado com sucesso\n")
        else:
            print("   ✗ Falha na renovação\n")
    else:
        print("   - Refresh token não disponível para teste\n")

    # Teste 6: Logout
    print("6. Realizando logout...")
    auth_service.logout()
    if not auth_service.is_authenticated:
        print("   ✓ Logout realizado\n")
    else:
        print("   ✗ Ainda autenticado\n")

    print("=== Testes concluídos ===")
