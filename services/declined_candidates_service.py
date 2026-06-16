"""
Serviço para gerenciamento de candidatos que declinaram
Fornece funcionalidades específicas para rastreamento e análise
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from models.database import Candidatura, Talento, Vaga, CandidaturaStatusEnum
from utils.logger import get_logger


class DeclinedCandidatesService:
    """Serviço para gerenciar candidatos que declinaram"""

    def __init__(self, session: Session):
        self.session = session
        self.logger = get_logger(__name__)

    def get_declined_candidates(
        self,
        vaga_id: Optional[int] = None,
        days_ago: Optional[int] = None,
        include_talent_details: bool = True
    ) -> List[Dict]:
        """
        Busca candidatos que declinaram

        Args:
            vaga_id: ID da vaga (opcional - filtra por vaga específica)
            days_ago: Número de dias atrás para filtrar (opcional)
            include_talent_details: Incluir detalhes do talento

        Returns:
            Lista de candidaturas com status declined
        """
        query = self.session.query(Candidatura).filter(
            Candidatura.status == CandidaturaStatusEnum.DECLINED
        )

        if vaga_id:
            query = query.filter(Candidatura.vaga_id == vaga_id)

        if days_ago:
            cutoff_date = datetime.utcnow() - timedelta(days=days_ago)
            query = query.filter(Candidatura.updated_at >= cutoff_date)

        if include_talent_details:
            query = query.join(Talento, Candidatura.talento_id == Talento.id, isouter=True)
            query = query.join(Vaga, Candidatura.vaga_id == Vaga.id)

        results = []
        for cand in query.all():
            result = {
                'candidatura_id': cand.inhire_id,
                'talent_inhire_id': cand.talent_inhire_id,
                'talent_name': cand.talent_name,
                'talent_email': cand.talent_email,
                'vaga_name': cand.vaga.name if cand.vaga else None,
                'vaga_id': cand.vaga.inhire_id if cand.vaga else None,
                'updated_at': cand.updated_at_inhire,
                'source': cand.source
            }

            if include_talent_details and cand.talento:
                result['talent_details'] = {
                    'phone': cand.talento.phone,
                    'headline': cand.talento.headline,
                    'company': cand.talento.company,
                    'location': cand.talento.location,
                    'linkedin': cand.talento.linkedin_username
                }

            results.append(result)

        self.logger.info(f"Encontrados {len(results)} candidatos que declinaram")
        return results

    def get_declined_stats_by_job(self) -> List[Dict]:
        """
        Estatísticas de candidatos que declinaram por vaga

        Returns:
            Lista com estatísticas por vaga
        """
        stats = (
            self.session.query(
                Vaga.inhire_id,
                Vaga.name,
                Vaga.status,
                func.count(Candidatura.id).label('declined_count')
            )
            .join(Candidatura, Candidatura.vaga_id == Vaga.id)
            .filter(Candidatura.status == CandidaturaStatusEnum.DECLINED)
            .group_by(Vaga.id, Vaga.inhire_id, Vaga.name, Vaga.status)
            .order_by(func.count(Candidatura.id).desc())
            .all()
        )

        results = []
        for stat in stats:
            results.append({
                'vaga_id': stat.inhire_id,
                'vaga_name': stat.name,
                'vaga_status': stat.status,
                'declined_count': stat.declined_count
            })

        self.logger.info(f"Estatísticas geradas para {len(results)} vagas")
        return results

    def get_declined_rate_by_job(self) -> List[Dict]:
        """
        Taxa de declínio (declined rate) por vaga

        Returns:
            Lista com taxa de declínio por vaga
        """
        # Subquery para contar total de candidaturas por vaga
        total_subq = (
            self.session.query(
                Candidatura.vaga_id,
                func.count(Candidatura.id).label('total_count')
            )
            .group_by(Candidatura.vaga_id)
            .subquery()
        )

        # Subquery para contar candidaturas declined por vaga
        declined_subq = (
            self.session.query(
                Candidatura.vaga_id,
                func.count(Candidatura.id).label('declined_count')
            )
            .filter(Candidatura.status == CandidaturaStatusEnum.DECLINED)
            .group_by(Candidatura.vaga_id)
            .subquery()
        )

        # Join e cálculo de taxa
        results = (
            self.session.query(
                Vaga.inhire_id,
                Vaga.name,
                total_subq.c.total_count,
                func.coalesce(declined_subq.c.declined_count, 0).label('declined_count')
            )
            .join(total_subq, total_subq.c.vaga_id == Vaga.id)
            .join(declined_subq, declined_subq.c.vaga_id == Vaga.id, isouter=True)
            .all()
        )

        output = []
        for row in results:
            declined_count = row.declined_count or 0
            total_count = row.total_count or 1
            decline_rate = (declined_count / total_count) * 100 if total_count > 0 else 0

            output.append({
                'vaga_id': row.inhire_id,
                'vaga_name': row.name,
                'total_candidaturas': total_count,
                'declined_count': declined_count,
                'decline_rate_percent': round(decline_rate, 2)
            })

        # Ordenar por taxa de declínio
        output.sort(key=lambda x: x['decline_rate_percent'], reverse=True)

        self.logger.info(f"Taxa de declínio calculada para {len(output)} vagas")
        return output

    def get_declined_reasons_analysis(self) -> Dict:
        """
        Análise de padrões em candidatos que declinaram

        Returns:
            Análise agregada de padrões
        """
        declined_candidates = self.session.query(Candidatura).filter(
            Candidatura.status == CandidaturaStatusEnum.DECLINED
        ).all()

        total = len(declined_candidates)

        # Análise por fonte (source)
        by_source = {}
        by_stage = {}
        by_phase = {}

        for cand in declined_candidates:
            # Por fonte
            source = cand.source or 'Unknown'
            by_source[source] = by_source.get(source, 0) + 1

            # Por stage
            stage = cand.stage_name or 'Unknown'
            by_stage[stage] = by_stage.get(stage, 0) + 1

            # Por phase
            phase = cand.phase_name or 'Unknown'
            by_phase[phase] = by_phase.get(phase, 0) + 1

        self.logger.info(f"Análise de padrões realizada para {total} candidatos declined")

        return {
            'total_declined': total,
            'by_source': dict(sorted(by_source.items(), key=lambda x: x[1], reverse=True)),
            'by_stage': dict(sorted(by_stage.items(), key=lambda x: x[1], reverse=True)),
            'by_phase': dict(sorted(by_phase.items(), key=lambda x: x[1], reverse=True))
        }

    def mark_candidates_to_reengage(self, days_ago: int = 90) -> List[str]:
        """
        Marca candidatos declined antigos para possível reengajamento

        Args:
            days_ago: Número de dias desde o declínio

        Returns:
            Lista de IDs de talentos para reengajamento
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_ago)

        candidates = self.session.query(Candidatura).filter(
            and_(
                Candidatura.status == CandidaturaStatusEnum.DECLINED,
                Candidatura.updated_at_inhire <= cutoff_date
            )
        ).all()

        talent_ids = list(set([c.talent_inhire_id for c in candidates]))

        self.logger.info(
            f"Identificados {len(talent_ids)} talentos para possível reengajamento "
            f"(declined há mais de {days_ago} dias)"
        )

        return talent_ids

    def export_declined_report(self, output_path: str = None) -> str:
        """
        Gera relatório CSV de candidatos declined

        Args:
            output_path: Caminho para salvar o CSV (opcional)

        Returns:
            Caminho do arquivo gerado
        """
        import csv
        from datetime import datetime

        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"declined_candidates_report_{timestamp}.csv"

        candidates = self.get_declined_candidates(include_talent_details=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if not candidates:
                self.logger.warning("Nenhum candidato declined para exportar")
                return output_path

            fieldnames = [
                'candidatura_id', 'talent_inhire_id', 'talent_name', 'talent_email',
                'vaga_name', 'vaga_id', 'updated_at', 'source',
                'talent_phone', 'talent_headline', 'talent_company',
                'talent_location', 'talent_linkedin'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for cand in candidates:
                row = {
                    'candidatura_id': cand['candidatura_id'],
                    'talent_inhire_id': cand['talent_inhire_id'],
                    'talent_name': cand['talent_name'],
                    'talent_email': cand['talent_email'],
                    'vaga_name': cand['vaga_name'],
                    'vaga_id': cand['vaga_id'],
                    'updated_at': cand['updated_at'],
                    'source': cand['source']
                }

                if 'talent_details' in cand:
                    details = cand['talent_details']
                    row.update({
                        'talent_phone': details.get('phone'),
                        'talent_headline': details.get('headline'),
                        'talent_company': details.get('company'),
                        'talent_location': details.get('location'),
                        'talent_linkedin': details.get('linkedin')
                    })

                writer.writerow(row)

        self.logger.info(f"Relatório exportado para: {output_path}")
        return output_path
