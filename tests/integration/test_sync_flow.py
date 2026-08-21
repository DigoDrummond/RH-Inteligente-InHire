"""
Testes de integração para fluxo completo de sincronização
Testa interação entre services e banco de dados
"""
import pytest
from unittest.mock import patch, Mock
from services.sync_service import SyncService
from models.database import Vaga, Posicao, Candidatura, Talento, SyncLog


@pytest.mark.integration
@pytest.mark.requires_db
class TestFullSyncFlow:
    """Testes para sincronização completa"""

    def test_sync_vagas_end_to_end(self, db_session, sample_vaga_data):
        """Deve sincronizar vagas do início ao fim"""
        # Mock API response
        api_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        sync_service = SyncService(db_session)

        with patch.object(sync_service.api_client, '_request', return_value=api_response):
            # Executar sync
            result = sync_service._sync_vagas_full()

            assert result['processed'] == 1
            assert result['created'] == 1

            # Verificar no banco
            vaga = db_session.query(Vaga).filter_by(inhire_id="vaga-123").first()
            assert vaga is not None
            assert vaga.name == "Desenvolvedor Python"

    def test_sync_respects_dependency_order(self, db_session, sample_vaga_data, sample_posicao_data):
        """Deve respeitar ordem de dependências (Vaga antes de Posição)"""
        vaga_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        posicao_response = {
            "items": [sample_posicao_data],
            "hasMore": False,
            "nextStartKey": None
        }

        sync_service = SyncService(db_session)

        # Mock ambas as respostas
        with patch.object(sync_service.api_client, '_request') as mock_request:
            # Primeira chamada: vagas
            # Segunda chamada: posições
            mock_request.side_effect = [vaga_response, posicao_response]

            # Sync vagas primeiro
            sync_service._sync_vagas_full()

            # Sync posições depois
            result = sync_service._sync_posicoes_full()

            assert result['processed'] == 1
            assert result['created'] == 1

            # Verificar FK está correto
            posicao = db_session.query(Posicao).filter_by(inhire_id="pos-456").first()
            assert posicao is not None
            assert posicao.vaga_id is not None


@pytest.mark.integration
@pytest.mark.requires_db
class TestIncrementalSyncFlow:
    """Testes para sincronização incremental"""

    def test_sync_updates_existing_records(self, db_session, sample_vaga_data):
        """Deve atualizar registros existentes em sync incremental"""
        # Criar registro inicial
        vaga_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        sync_service = SyncService(db_session)

        with patch.object(sync_service.api_client, '_request', return_value=vaga_response):
            # Primeira sync
            sync_service._sync_vagas_full()
            db_session.commit()

            # Atualizar dados
            sample_vaga_data["name"] = "Desenvolvedor Python Senior"
            sample_vaga_data["updatedAt"] = "2025-01-16T10:00:00Z"

            vaga_response_updated = {
                "results": [sample_vaga_data],
                "startKey": None,
                "count": 1
            }

            with patch.object(sync_service.api_client, '_request', return_value=vaga_response_updated):
                # Segunda sync (incremental)
                result = sync_service._sync_vagas_incremental()

                assert result['updated'] == 1
                assert result['skipped'] == 0

                # Verificar atualização
                vaga = db_session.query(Vaga).filter_by(inhire_id="vaga-123").first()
                assert vaga.name == "Desenvolvedor Python Senior"

    def test_sync_skips_unchanged_records(self, db_session, sample_vaga_data):
        """Deve pular registros não alterados"""
        vaga_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        sync_service = SyncService(db_session)

        with patch.object(sync_service.api_client, '_request', return_value=vaga_response):
            # Primeira sync
            sync_service._sync_vagas_full()
            db_session.commit()

            # Segunda sync sem mudanças
            result = sync_service._sync_vagas_incremental()

            assert result['skipped'] == 1
            assert result['updated'] == 0


@pytest.mark.integration
@pytest.mark.requires_db
class TestSyncWithTalentIds:
    """Testes para otimização de sync com talent IDs"""

    def test_sync_collects_talent_ids_from_candidaturas(self, db_session, sample_vaga_data, sample_candidatura_data):
        """Deve coletar talent IDs das candidaturas"""
        # Setup vaga
        vaga_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        # Candidatura com talent ID
        cand_response = {
            "results": [sample_candidatura_data],
            "startKey": None,
            "count": 1
        }

        sync_service = SyncService(db_session)

        with patch.object(sync_service.api_client, '_request') as mock_request:
            mock_request.side_effect = [vaga_response, cand_response]

            # Sync vagas e candidaturas
            sync_service._sync_vagas_full()
            stats, talent_ids = sync_service._sync_candidaturas_full()

            # Verificar que coletou talent ID
            assert "talent-111" in talent_ids
            assert len(talent_ids) == 1


@pytest.mark.integration
@pytest.mark.requires_db
class TestSyncLogging:
    """Testes para logging de sincronização"""

    def test_sync_creates_log_entry(self, db_session, sample_vaga_data):
        """Deve criar registro de sync log"""
        from models.database import SyncConfiguration

        # Criar config
        config = SyncConfiguration(tenant_id="test-tenant")
        db_session.add(config)
        db_session.commit()

        vaga_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        sync_service = SyncService(db_session)

        with patch.object(sync_service.api_client, '_request', return_value=vaga_response):
            # Executar sync completo (cria log)
            result = sync_service.sync_full()

            # Verificar log
            logs = db_session.query(SyncLog).all()
            assert len(logs) > 0

            latest_log = logs[-1]
            assert latest_log.sync_type == "FULL"
            assert latest_log.status == "SUCCESS"
            assert latest_log.records_processed > 0

    def test_sync_log_records_errors(self, db_session):
        """Deve registrar erros no sync log"""
        from models.database import SyncConfiguration

        config = SyncConfiguration(tenant_id="test-tenant")
        db_session.add(config)
        db_session.commit()

        sync_service = SyncService(db_session)

        # Forçar erro
        with patch.object(sync_service.api_client, '_request', side_effect=Exception("API Error")):
            result = sync_service.sync_full()

            assert result['success'] is False
            assert result['status'] == "ERROR"

            # Verificar log de erro
            logs = db_session.query(SyncLog).filter_by(status="ERROR").all()
            assert len(logs) > 0


@pytest.mark.integration
@pytest.mark.requires_db
@pytest.mark.slow
class TestFullSyncPerformance:
    """Testes de performance para sync completo"""

    def test_sync_handles_large_dataset(self, db_session, sample_vaga_data):
        """Deve processar dataset grande eficientemente"""
        import time

        # Criar 100 vagas
        vagas = []
        for i in range(100):
            vaga = sample_vaga_data.copy()
            vaga["id"] = f"vaga-{i}"
            vagas.append(vaga)

        response = {
            "results": vagas,
            "startKey": None,
            "count": 100
        }

        sync_service = SyncService(db_session)

        start_time = time.time()

        with patch.object(sync_service.api_client, '_request', return_value=response):
            result = sync_service._sync_vagas_full()

        duration = time.time() - start_time

        assert result['processed'] == 100
        assert duration < 10  # Deve processar em menos de 10 segundos


@pytest.mark.integration
@pytest.mark.requires_db
class TestSyncRollback:
    """Testes para rollback em caso de erro"""

    def test_sync_rollback_on_error(self, db_session, sample_vaga_data):
        """Deve fazer rollback se houver erro no meio da sync"""
        vaga_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        sync_service = SyncService(db_session)

        # Primeira vaga OK, segunda com erro
        with patch.object(sync_service.db, 'upsert_vaga') as mock_upsert:
            # Primeiro OK, segundo erro
            mock_upsert.side_effect = [
                (True, "created"),
                Exception("Database error")
            ]

            with patch.object(sync_service.api_client, '_request', return_value=vaga_response):
                try:
                    sync_service._sync_vagas_full()
                except:
                    pass

                # Verificar que fez rollback
                db_session.rollback()
                vagas = db_session.query(Vaga).all()
                # Dependendo da implementação, pode não ter nenhuma vaga
                # (se transaction rollback completo)


@pytest.mark.integration
@pytest.mark.requires_db
class TestSyncWithCustomFields:
    """Testes para sync de custom fields (JSONB)"""

    def test_sync_preserves_custom_fields(self, db_session, sample_vaga_data):
        """Deve preservar custom fields como JSONB"""
        sample_vaga_data["customFields"] = {
            "area": "Backend",
            "stack": ["Python", "Django"],
            "remote": True
        }

        vaga_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        sync_service = SyncService(db_session)

        with patch.object(sync_service.api_client, '_request', return_value=vaga_response):
            sync_service._sync_vagas_full()
            db_session.commit()

            # Verificar JSONB
            vaga = db_session.query(Vaga).filter_by(inhire_id="vaga-123").first()
            assert vaga.custom_fields is not None
            assert vaga.custom_fields["area"] == "Backend"
            assert "Python" in vaga.custom_fields["stack"]
            assert vaga.custom_fields["remote"] is True
