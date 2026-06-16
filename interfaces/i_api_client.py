"""
Interface abstrata para API Client
Permite injetar diferentes implementações de API clients
"""
from abc import ABC, abstractmethod
from typing import Generator, Optional, Dict
from models.api_schemas import VagaAPI, PosicaoAPI, CandidaturaAPI, TalentoAPI


class IAPIClient(ABC):
    """Interface para clientes de API"""

    @abstractmethod
    def validate_tenant(self) -> bool:
        """Valida se tenant configurado existe"""
        pass

    @abstractmethod
    def get_all_vagas(self, tenant_id: str = None, limit: int = None) -> Generator[VagaAPI, None, None]:
        """Retorna generator de vagas"""
        pass

    @abstractmethod
    def get_all_posicoes(self, job_id: str, limit: int = None) -> Generator[PosicaoAPI, None, None]:
        """Retorna generator de posições de uma vaga"""
        pass

    @abstractmethod
    def get_all_candidaturas(self, job_id: str, limit: int = None) -> Generator[CandidaturaAPI, None, None]:
        """Retorna generator de candidaturas de uma vaga"""
        pass

    @abstractmethod
    def get_talento_by_id(self, talent_id: str) -> Optional[TalentoAPI]:
        """Busca talento por ID"""
        pass

    @abstractmethod
    def get_all_talentos(self, limit: int = None, filter_dict: Dict = None) -> Generator[TalentoAPI, None, None]:
        """Retorna generator de talentos"""
        pass

    @abstractmethod
    def get_candidatura_timeline(self, candidatura_id: str) -> list:
        """Busca timeline de uma candidatura"""
        pass
