"""
Script para adicionar método de sincronização de talentos faltantes ao sync_service.py
"""

NEW_METHOD = '''
    def _sync_missing_talentos(self) -> Dict:
        """
        SINCRONIZAÇÃO DE TALENTOS FALTANTES

        Busca talent_inhire_id que existem em candidaturas mas não na tabela talentos,
        e os sincroniza da API.

        Útil para:
        - Talentos criados recentemente que ainda não foram sincronizados
        - Talentos antigos que podem ter sido pulados em syncs anteriores
        - Garantir que todos os talentos em candidaturas existam na tabela
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Talento, Candidatura
        from sqlalchemy import func

        try:
            # 1. Buscar talent_inhire_id que existem em candidaturas mas não em talentos
            self.logger.info("   Identificando talentos faltantes...")

            subquery = self.session.query(Talento.inhire_id).subquery()

            missing_talent_ids = self.session.query(
                func.distinct(Candidatura.talent_inhire_id)
            ).filter(
                Candidatura.talent_inhire_id.isnot(None),
                ~Candidatura.talent_inhire_id.in_(subquery)
            ).all()

            missing_ids = [row[0] for row in missing_talent_ids]

            if not missing_ids:
                self.logger.info("   ✓ Nenhum talento faltante encontrado")
                return stats

            self.logger.info(f"   Encontrados {len(missing_ids)} talentos faltantes")

            # 2. Buscar cada talento faltante da API
            for i, talent_id in enumerate(missing_ids, 1):
                try:
                    # Buscar talento individual da API
                    talento_api = self.api_client.get_talento_by_id(talent_id)

                    if talento_api:
                        # Inserir na tabela
                        is_new, operation = self.db.upsert_talento(talento_api)
                        stats['processed'] += 1
                        stats[operation] += 1
                    else:
                        # Talento não encontrado na API (pode ter sido deletado)
                        stats['skipped'] += 1

                    # Log de progresso a cada 50 talentos
                    if i % 50 == 0:
                        self.logger.info(f"   Talentos faltantes sincronizados: {i}/{len(missing_ids)}")

                except Exception as e:
                    stats['failed'] += 1
                    self.logger.warning(f"   Erro ao sincronizar talento faltante {talent_id}: {str(e)}")

            self.logger.info(f"   ✓ Talentos faltantes sincronizados: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Erro ao sincronizar talentos faltantes: {str(e)}")
            return stats
'''

# Localização onde adicionar (logo após o método _sync_talentos_incremental_optimized)
INSERT_AFTER_LINE = 1653  # Linha após o método _sync_talentos_incremental_optimized

print("=" * 80)
print("NOVO MÉTODO PARA SYNC_SERVICE.PY")
print("=" * 80)
print()
print("Adicione o seguinte método após a linha", INSERT_AFTER_LINE)
print("(logo após o método _sync_talentos_incremental_optimized)")
print()
print(NEW_METHOD)
print()
print("=" * 80)
print("CHAMADAS NO SYNC INCREMENTAL")
print("=" * 80)
print()
print("Adicione as seguintes chamadas após o sync de talentos normal:")
print()

CALL_IN_EXPRESS = '''
                # 5.1 TALENTOS FALTANTES (apenas os que não existem na tabela)
                if settings.SYNC_TALENTOS_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando TALENTOS FALTANTES...")
                        missing_tal_stats = self._sync_missing_talentos()
                        self._merge_stats(all_stats, missing_tal_stats)
                    except Exception as e:
                        self.logger.warning(f"Erro ao sincronizar talentos faltantes: {str(e)}")
'''

CALL_IN_COMPLETE = '''
                # 5.1 TALENTOS FALTANTES (apenas os que não existem na tabela)
                if settings.SYNC_TALENTOS_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando TALENTOS FALTANTES...")
                        missing_tal_stats = self._sync_missing_talentos()
                        self._merge_stats(all_stats, missing_tal_stats)
                    except Exception as e:
                        self.logger.warning(f"Erro ao sincronizar talentos faltantes: {str(e)}")
'''

print("NO MODO EXPRESS (após linha ~419):")
print(CALL_IN_EXPRESS)
print()
print("NO MODO COMPLETO (após linha ~534):")
print(CALL_IN_COMPLETE)
print()
print("=" * 80)
print("ADICIONAR MÉTODO NA API_CLIENT.PY")
print("=" * 80)
print()

API_METHOD = '''
    def get_talento_by_id(self, talent_id: str) -> Optional[TalentoAPI]:
        """
        Busca um talento específico pelo ID

        Args:
            talent_id: UUID do talento no InHire

        Returns:
            TalentoAPI ou None se não encontrado
        """
        try:
            response = self._request("GET", f"{InhireEndpoints.TALENTS}/{talent_id}")

            if response:
                return TalentoAPI(**response)
            return None

        except Exception as e:
            self.logger.error(f"Erro ao buscar talento {talent_id}: {str(e)}")
            return None
'''

print("Adicione este método na classe InhireAPIClient (api_client.py):")
print(API_METHOD)
print()
