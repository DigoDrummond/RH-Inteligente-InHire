"""
Candidatura Repository - Operações de persistência para Candidaturas
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from repositories.base_repository import BaseRepository
from models.database import Candidatura


class CandidaturaRepository(BaseRepository[Candidatura]):
    """Repository para entidade Candidatura"""

    @property
    def model_class(self):
        return Candidatura

    def get_by_vaga_id(self, vaga_id: int) -> List[Candidatura]:
        """
        Busca todas as candidaturas de uma vaga

        Args:
            vaga_id: ID da vaga (FK)

        Returns:
            Lista de candidaturas
        """
        try:
            return self.session.query(Candidatura).filter_by(vaga_id=vaga_id).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar candidaturas da vaga {vaga_id}: {e}")
            return []

    def get_by_talento_id(self, talento_id: int) -> List[Candidatura]:
        """
        Busca todas as candidaturas de um talento

        Args:
            talento_id: ID do talento (FK)

        Returns:
            Lista de candidaturas
        """
        try:
            return self.session.query(Candidatura).filter_by(talento_id=talento_id).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar candidaturas do talento {talento_id}: {e}")
            return []

    def get_by_status(self, status: str) -> List[Candidatura]:
        """
        Busca candidaturas por status

        Args:
            status: Status da candidatura

        Returns:
            Lista de candidaturas
        """
        try:
            return self.session.query(Candidatura).filter_by(status=status).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar candidaturas com status {status}: {e}")
            return []

    def get_active(self) -> List[Candidatura]:
        """
        Busca candidaturas ativas

        Returns:
            Lista de candidaturas ativas
        """
        try:
            return self.session.query(Candidatura).filter_by(status='active').all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar candidaturas ativas: {e}")
            return []

    def get_hired(self) -> List[Candidatura]:
        """
        Busca candidaturas contratadas

        Returns:
            Lista de candidaturas contratadas
        """
        try:
            return self.session.query(Candidatura).filter_by(status='hired').all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar candidaturas contratadas: {e}")
            return []

    def get_updated_since(self, since_date: datetime, status: Optional[str] = None) -> List[Candidatura]:
        """
        Busca candidaturas atualizadas desde uma data

        Args:
            since_date: Data de referência
            status: Filtro de status opcional

        Returns:
            Lista de candidaturas atualizadas
        """
        try:
            query = self.session.query(Candidatura).filter(
                Candidatura.updated_at_inhire >= since_date
            )
            if status:
                query = query.filter_by(status=status)
            return query.all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar candidaturas atualizadas desde {since_date}: {e}")
            return []

    def get_all_talent_ids(self) -> set:
        """
        Busca todos os talent_id únicos das candidaturas

        Returns:
            Set de talent_ids
        """
        try:
            results = self.session.query(Candidatura.talent_id).filter(
                Candidatura.talent_id.isnot(None)
            ).distinct().all()
            return {r[0] for r in results}
        except Exception as e:
            self.logger.error(f"Erro ao buscar talent_ids: {e}")
            return set()

    def count_by_vaga(self, vaga_id: int) -> int:
        """
        Conta candidaturas de uma vaga

        Args:
            vaga_id: ID da vaga

        Returns:
            Quantidade de candidaturas
        """
        try:
            return self.session.query(Candidatura).filter_by(vaga_id=vaga_id).count()
        except Exception as e:
            self.logger.error(f"Erro ao contar candidaturas da vaga {vaga_id}: {e}")
            return 0

    def count_by_status(self, status: str) -> int:
        """
        Conta candidaturas por status

        Args:
            status: Status da candidatura

        Returns:
            Quantidade de candidaturas
        """
        try:
            return self.session.query(Candidatura).filter_by(status=status).count()
        except Exception as e:
            self.logger.error(f"Erro ao contar candidaturas com status {status}: {e}")
            return 0
