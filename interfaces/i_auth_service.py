"""
Interface abstrata para Auth Service
Permite injetar diferentes implementações de autenticação
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class IAuthService(ABC):
    """Interface para serviços de autenticação"""

    @abstractmethod
    def login(self) -> bool:
        """Faz login e obtém tokens"""
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """Autentica ou reautentica se necessário"""
        pass

    @abstractmethod
    def ensure_authenticated(self) -> None:
        """Garante que está autenticado"""
        pass

    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """Retorna headers de autenticação"""
        pass

    @abstractmethod
    def is_token_valid(self) -> bool:
        """Verifica se token ainda é válido"""
        pass

    @abstractmethod
    def refresh_token(self) -> bool:
        """Renova o access token usando refresh token"""
        pass
