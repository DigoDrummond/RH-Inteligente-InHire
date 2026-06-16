"""
Vaga Repository - Operações de persistência para Vagas
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from repositories.base_repository import BaseRepository
from models.database import Vaga


class VagaRepository(BaseRepository[Vaga]):
    """Repository para entidade Vaga"""

    @property
    def model_class(self):
        return Vaga

    def get_all_open(self) -> List[Vaga]:
        """
        Busca todas as vagas abertas

        Returns:
            Lista de vagas com status 'open'
        """
        try:
            return self.session.query(Vaga).filter(Vaga.status == 'open').all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar vagas abertas: {e}")
            return []

    def get_by_department(self, department: str) -> List[Vaga]:
        """
        Busca vagas por departamento

        Args:
            department: Nome do departamento

        Returns:
            Lista de vagas do departamento
        """
        try:
            return self.session.query(Vaga).filter(Vaga.department == department).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar vagas por departamento {department}: {e}")
            return []

    def get_updated_since(self, since_date: datetime) -> List[Vaga]:
        """
        Busca vagas atualizadas desde uma data

        Args:
            since_date: Data de referência

        Returns:
            Lista de vagas atualizadas
        """
        try:
            return self.session.query(Vaga).filter(
                Vaga.updated_at_inhire >= since_date
            ).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar vagas atualizadas desde {since_date}: {e}")
            return []

    def get_all_inhire_ids(self) -> List[str]:
        """
        Busca todos os inhire_ids de vagas (para cache de FK)

        Returns:
            Lista de inhire_ids
        """
        try:
            results = self.session.query(Vaga.inhire_id).all()
            return [r[0] for r in results]
        except Exception as e:
            self.logger.error(f"Erro ao buscar inhire_ids de vagas: {e}")
            return []

    def get_id_by_inhire_id(self, inhire_id: str) -> Optional[int]:
        """
        Busca apenas o ID interno por inhire_id (otimizado para FK)

        Args:
            inhire_id: ID da API Inhire

        Returns:
            ID interno ou None
        """
        try:
            result = self.session.query(Vaga.id).filter_by(inhire_id=inhire_id).first()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Erro ao buscar ID de vaga por inhire_id {inhire_id}: {e}")
            return None

    def get_all_id_mappings(self) -> dict:
        """
        Busca todos os mapeamentos inhire_id -> db_id (para cache)

        Returns:
            Dict {inhire_id: db_id}
        """
        try:
            results = self.session.query(Vaga.inhire_id, Vaga.id).all()
            return {r.inhire_id: r.id for r in results}
        except Exception as e:
            self.logger.error(f"Erro ao buscar mapeamentos de IDs de vagas: {e}")
            return {}

    def get_vagas_com_posicoes_abertas(self) -> List[Vaga]:
        """
        Busca vagas que têm pelo menos 1 posição aberta

        Returns:
            Lista de vagas com posições abertas
        """
        try:
            from models.database import Posicao
            from sqlalchemy import exists, select

            # Usar subconsulta para evitar DISTINCT em colunas JSON
            subq = (
                select(Posicao.vaga_id)
                .where(Posicao.status == 'open')
                .distinct()
            )

            return (
                self.session.query(Vaga)
                .filter(Vaga.id.in_(subq))
                .all()
            )
        except Exception as e:
            self.logger.error(f"Erro ao buscar vagas com posições abertas: {e}")
            return []

    def get_vagas_ativas_ou_recentes(self, days: int = 7) -> List[Vaga]:
        """
        Busca vagas ativas (status=open) OU atualizadas nos últimos N dias

        Args:
            days: Número de dias para considerar como 'recente'

        Returns:
            Lista de vagas ativas ou recentes
        """
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import or_

            cutoff = datetime.now() - timedelta(days=days)

            return (
                self.session.query(Vaga)
                .filter(
                    or_(
                        Vaga.status == 'OPEN',  # Status é ENUM em uppercase
                        Vaga.updated_at_inhire > cutoff
                    )
                )
                .all()
            )
        except Exception as e:
            self.logger.error(f"Erro ao buscar vagas ativas ou recentes: {e}")
            return []
