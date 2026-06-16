"""
Talento Repository - Operações de persistência para Talentos
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from repositories.base_repository import BaseRepository
from models.database import Talento


class TalentoRepository(BaseRepository[Talento]):
    """Repository para entidade Talento"""

    @property
    def model_class(self):
        return Talento

    def get_by_email(self, email: str) -> Optional[Talento]:
        """
        Busca talento por email

        Args:
            email: Email do talento

        Returns:
            Talento encontrado ou None
        """
        try:
            return self.session.query(Talento).filter_by(email=email).first()
        except Exception as e:
            self.logger.error(f"Erro ao buscar talento por email {email}: {e}")
            return None

    def get_by_phone(self, phone: str) -> Optional[Talento]:
        """
        Busca talento por telefone

        Args:
            phone: Telefone do talento

        Returns:
            Talento encontrado ou None
        """
        try:
            return self.session.query(Talento).filter_by(phone=phone).first()
        except Exception as e:
            self.logger.error(f"Erro ao buscar talento por telefone {phone}: {e}")
            return None

    def get_updated_since(self, since_date: datetime) -> List[Talento]:
        """
        Busca talentos atualizados desde uma data

        Args:
            since_date: Data de referência

        Returns:
            Lista de talentos atualizados
        """
        try:
            return self.session.query(Talento).filter(
                Talento.updated_at_inhire >= since_date
            ).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar talentos atualizados desde {since_date}: {e}")
            return []

    def search_by_name(self, name: str) -> List[Talento]:
        """
        Busca talentos por nome (case-insensitive, partial match)

        Args:
            name: Nome a buscar

        Returns:
            Lista de talentos encontrados
        """
        try:
            return self.session.query(Talento).filter(
                Talento.name.ilike(f"%{name}%")
            ).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar talentos por nome {name}: {e}")
            return []

    def get_all_id_mappings(self) -> dict:
        """
        Busca todos os mapeamentos inhire_id -> db_id (para cache)

        Returns:
            Dict {inhire_id: db_id}
        """
        try:
            results = self.session.query(Talento.inhire_id, Talento.id).all()
            return {r.inhire_id: r.id for r in results}
        except Exception as e:
            self.logger.error(f"Erro ao buscar mapeamentos de IDs de talentos: {e}")
            return {}

    def get_id_by_inhire_id(self, inhire_id: str) -> Optional[int]:
        """
        Busca apenas o ID interno por inhire_id (otimizado para FK)

        Args:
            inhire_id: ID da API Inhire

        Returns:
            ID interno ou None
        """
        try:
            result = self.session.query(Talento.id).filter_by(inhire_id=inhire_id).first()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Erro ao buscar ID de talento por inhire_id {inhire_id}: {e}")
            return None

    def count_with_email(self) -> int:
        """
        Conta talentos que têm email

        Returns:
            Quantidade de talentos com email
        """
        try:
            return self.session.query(Talento).filter(
                Talento.email.isnot(None)
            ).count()
        except Exception as e:
            self.logger.error(f"Erro ao contar talentos com email: {e}")
            return 0
