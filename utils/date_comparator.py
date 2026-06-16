"""
DateComparator: Utilit&#225;rio centralizado para compara&#231;&#227;o de datas
Extrai l&#243;gica duplicada de compara&#231;&#227;o de datas do SyncService
"""
from datetime import datetime, timezone
from typing import Optional
import pytz
from dateutil import parser
from utils.logger import get_logger


class DateComparator:
    """
    Centraliza l&#243;gica de compara&#231;&#227;o de datas para sync incremental.

    Respons&#225;vel por:
    - Normalizar datas para timezone consistente (S&#227;o Paulo)
    - Comparar datas de API vs banco
    - Determinar se entidade deve ser atualizada
    """

    def __init__(self, timezone_name: str = 'America/Sao_Paulo'):
        """
        Args:
            timezone_name: Nome do timezone para normaliza&#231;&#227;o (default: S&#227;o Paulo)
        """
        self.timezone = pytz.timezone(timezone_name)
        self.logger = get_logger(__name__)

    def normalize(self, dt: Optional[datetime | str]) -> Optional[datetime]:
        """
        Normaliza datetime para timezone-naive em hor&#225;rio configurado.

        Args:
            dt: Datetime object ou string ISO 8601

        Returns:
            Datetime naive no timezone configurado, ou None

        Example:
            >>> comparator = DateComparator()
            >>> comparator.normalize("2025-01-20T10:00:00Z")
            datetime(2025, 20, 1, 7, 0, 0)  # -3h para SP
        """
        if dt is None:
            return None

        # Se for string, converter para datetime primeiro
        if isinstance(dt, str):
            try:
                dt = parser.isoparse(dt)
            except Exception as e:
                self.logger.warning(f"Erro ao parsear data '{dt}': {e}")
                return None

        # Se tem timezone, converter para o timezone configurado
        if dt.tzinfo is not None:
            dt_local = dt.astimezone(self.timezone)
            # Remover timezone info mantendo hor&#225;rio local
            return dt_local.replace(tzinfo=None)

        # Se j&#225; &#233; naive, assume que est&#225; no timezone correto
        return dt

    def is_newer(
        self,
        api_date: Optional[datetime | str],
        db_date: Optional[datetime]
    ) -> bool:
        """
        Verifica se data da API &#233; mais recente que data do banco.

        Args:
            api_date: Data vinda da API (pode ser string ou datetime)
            db_date: Data armazenada no banco (datetime naive)

        Returns:
            True se API &#233; mais recente, False caso contr&#225;rio

        Example:
            >>> comparator = DateComparator()
            >>> comparator.is_newer("2025-01-20T10:00:00Z", datetime(2025, 1, 19, 10, 0))
            True
        """
        if api_date is None or db_date is None:
            # Se alguma data &#233; None, considerar como "atualizar"
            return True

        api_normalized = self.normalize(api_date)
        if api_normalized is None:
            return False

        return api_normalized > db_date

    def should_update(
        self,
        api_updated_at: Optional[datetime | str],
        db_updated_at: Optional[datetime]
    ) -> bool:
        """
        Determina se registro deve ser atualizado baseado em datas.

        &#201; um alias mais sem&#226;ntico para is_newer().

        Args:
            api_updated_at: updated_at da API
            db_updated_at: updated_at do banco

        Returns:
            True se deve atualizar, False para pular
        """
        return self.is_newer(api_updated_at, db_updated_at)

    def is_equal_or_older(
        self,
        api_date: Optional[datetime | str],
        db_date: Optional[datetime]
    ) -> bool:
        """
        Verifica se data da API &#233; igual ou mais antiga que data do banco.

        Args:
            api_date: Data da API
            db_date: Data do banco

        Returns:
            True se API &#233; igual ou mais antiga (n&#227;o deve atualizar)
        """
        return not self.is_newer(api_date, db_date)

    def get_age_in_days(self, dt: Optional[datetime | str]) -> Optional[float]:
        """
        Calcula idade de uma data em dias.

        Args:
            dt: Data para calcular idade

        Returns:
            N&#250;mero de dias desde a data, ou None se data inv&#225;lida

        Example:
            >>> comparator = DateComparator()
            >>> comparator.get_age_in_days("2025-01-19T10:00:00Z")
            1.0  # Se hoje &#233; 20/01/2025
        """
        normalized = self.normalize(dt)
        if normalized is None:
            return None

        now = datetime.now()
        delta = now - normalized
        return delta.total_seconds() / 86400  # segundos para dias

    def filter_by_date_range(
        self,
        records: list,
        date_field: str,
        start_date: Optional[datetime | str] = None,
        end_date: Optional[datetime | str] = None
    ) -> list:
        """
        Filtra lista de registros por range de datas.

        Args:
            records: Lista de objetos com campo de data
            date_field: Nome do atributo de data no objeto
            start_date: Data inicial (inclusive)
            end_date: Data final (inclusive)

        Returns:
            Lista filtrada de registros

        Example:
            >>> records = [Record(updated_at="2025-01-19"), Record(updated_at="2025-01-20")]
            >>> comparator.filter_by_date_range(records, "updated_at", start_date="2025-01-20")
            [Record(updated_at="2025-01-20")]
        """
        start_normalized = self.normalize(start_date) if start_date else None
        end_normalized = self.normalize(end_date) if end_date else None

        filtered = []
        for record in records:
            record_date = getattr(record, date_field, None)
            if record_date is None:
                continue

            record_normalized = self.normalize(record_date)
            if record_normalized is None:
                continue

            # Verificar ranges
            if start_normalized and record_normalized < start_normalized:
                continue
            if end_normalized and record_normalized > end_normalized:
                continue

            filtered.append(record)

        return filtered

    def get_most_recent(self, dates: list[datetime | str | None]) -> Optional[datetime]:
        """
        Retorna a data mais recente de uma lista.

        Args:
            dates: Lista de datas (podem conter None)

        Returns:
            Data mais recente normalizada, ou None se lista vazia
        """
        normalized_dates = [self.normalize(d) for d in dates if d is not None]
        normalized_dates = [d for d in normalized_dates if d is not None]

        if not normalized_dates:
            return None

        return max(normalized_dates)

    def format_for_api(self, dt: Optional[datetime]) -> Optional[str]:
        """
        Formata datetime para envio &#224; API (ISO 8601 UTC).

        Args:
            dt: Datetime naive (assume timezone configurado)

        Returns:
            String ISO 8601 com timezone UTC

        Example:
            >>> comparator = DateComparator()
            >>> comparator.format_for_api(datetime(2025, 1, 20, 10, 0))
            "2025-01-20T13:00:00Z"  # +3h para UTC
        """
        if dt is None:
            return None

        # Adicionar timezone se naive
        if dt.tzinfo is None:
            dt_with_tz = self.timezone.localize(dt)
        else:
            dt_with_tz = dt

        # Converter para UTC e formatar
        dt_utc = dt_with_tz.astimezone(pytz.UTC)
        return dt_utc.isoformat().replace('+00:00', 'Z')


# Singleton global para uso em todo o projeto
_default_comparator = DateComparator()


def get_date_comparator() -> DateComparator:
    """
    Retorna inst&#226;ncia singleton do DateComparator.

    Returns:
        DateComparator configurado com timezone S&#227;o Paulo
    """
    return _default_comparator


# Conven&#234;ncia: expor fun&#231;&#245;es mais usadas no n&#237;vel do m&#243;dulo
normalize_date = _default_comparator.normalize
is_newer = _default_comparator.is_newer
should_update = _default_comparator.should_update
