"""
Interface abstrata para Database Service
Permite injetar diferentes implementações de persistência
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from models.api_schemas import VagaAPI, PosicaoAPI, CandidaturaAPI, TalentoAPI


class IDatabaseService(ABC):
    """Interface para serviços de banco de dados"""

    @abstractmethod
    def populate_fk_cache(self) -> None:
        """Popula cache de foreign keys"""
        pass

    @abstractmethod
    def clear_fk_cache(self) -> None:
        """Limpa cache de foreign keys"""
        pass

    @abstractmethod
    def batch_commit(self, batch_size: int = 50) -> None:
        """Commit em batch"""
        pass

    @abstractmethod
    def create_savepoint(self, name: str) -> None:
        """Cria savepoint na transação"""
        pass

    @abstractmethod
    def rollback_to_savepoint(self, name: str = None) -> None:
        """Rollback para savepoint"""
        pass

    @abstractmethod
    def release_savepoint(self, name: str = None) -> None:
        """Libera savepoint"""
        pass

    @abstractmethod
    def upsert_vaga(self, vaga_api: VagaAPI, commit=True) -> Tuple[bool, str]:
        """Insere ou atualiza vaga"""
        pass

    @abstractmethod
    def upsert_posicao(self, posicao_api: PosicaoAPI, commit=True) -> Tuple[bool, str]:
        """Insere ou atualiza posição"""
        pass

    @abstractmethod
    def upsert_candidatura(self, cand_api: CandidaturaAPI, job_id: str, commit=True) -> Tuple[bool, str]:
        """Insere ou atualiza candidatura"""
        pass

    @abstractmethod
    def upsert_talento(self, talento_api: TalentoAPI, commit=True) -> Tuple[bool, str]:
        """Insere ou atualiza talento"""
        pass

    @abstractmethod
    def upsert_candidatura_timeline(
        self,
        timeline_event: dict,
        candidatura_inhire_id: str,
        candidatura_db_id: int
    ) -> Tuple[bool, str]:
        """Insere ou atualiza evento de timeline"""
        pass

    @abstractmethod
    def get_vaga_id_cached(self, inhire_id: str) -> Optional[int]:
        """Busca vaga_id usando cache"""
        pass

    @abstractmethod
    def get_talento_id_cached(self, inhire_id: str) -> Optional[int]:
        """Busca talento_id usando cache"""
        pass
