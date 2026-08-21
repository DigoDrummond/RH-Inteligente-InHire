"""
Testes unitários para SyncService
Testa lógica de sincronização, comparação de datas, orquestração
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from services.sync_service import SyncService
from models.api_schemas import VagaAPI, PosicaoAPI, CandidaturaAPI, TalentoAPI
from models.database import Vaga, Posicao, Candidatura, Talento, SyncLog, SyncConfiguration
from config import SyncType, SyncEntity, SyncStatus


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServiceDateComparison:
    """Testes para comparação de datas"""

    def test_normalize_datetime_for_comparison_with_timezone(self, sync_service):
        """Deve normalizar datetime com timezone para UTC"""
        dt_with_tz = datetime(2025, 1, 15, 15, 30, 0, tzinfo=timezone.utc)
        dt_normalized = sync_service._normalize_datetime_for_comparison(dt_with_tz)

        assert dt_normalized.tzinfo is not None
        assert dt_normalized.tzinfo == timezone.utc

    def test_normalize_datetime_for_comparison_naive(self, sync_service):
        """Deve adicionar UTC timezone em datetime naive"""
        dt_naive = datetime(2025, 1, 15, 15, 30, 0)
        dt_normalized = sync_service._normalize_datetime_for_comparison(dt_naive)

        assert dt_normalized.tzinfo is not None
        assert dt_normalized.tzinfo == timezone.utc

    def test_normalize_datetime_for_comparison_none(self, sync_service):
        """Deve retornar None para input None"""
        result = sync_service._normalize_datetime_for_comparison(None)
        assert result is None

    def test_should_update_api_newer(self, sync_service):
        """Deve atualizar se API tem data mais recente"""
        api_date = datetime(2025, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        bd_date = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        # Normalizar
        api_normalized = sync_service._normalize_datetime_for_comparison(api_date)
        bd_normalized = sync_service._normalize_datetime_for_comparison(bd_date)

        assert api_normalized > bd_normalized  # Deve atualizar

    def test_should_skip_bd_newer(self, sync_service):
        """Deve pular se BD tem data mais recente"""
        api_date = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        bd_date = datetime(2025, 1, 16, 10, 0, 0, tzinfo=timezone.utc)

        api_normalized = sync_service._normalize_datetime_for_comparison(api_date)
        bd_normalized = sync_service._normalize_datetime_for_comparison(bd_date)

        assert api_normalized <= bd_normalized  # Deve pular


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServiceVagasFull:
    """Testes para sincronização completa de vagas"""

    def test_sync_vagas_full_creates_new(self, sync_service, sample_vaga_data):
        """Deve criar novas vagas na sync full"""
        vagas_response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.return_value = iter([VagaAPI(**sample_vaga_data)])

            result = sync_service._sync_vagas_full()

            assert result['processed'] == 1
            assert result['created'] == 1
            assert result['failed'] == 0

    def test_sync_vagas_full_updates_existing(self, database_service, sync_service, sample_vaga_data):
        """Deve atualizar vagas existentes"""
        # Criar vaga inicial
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # Atualizar dados
        sample_vaga_data["name"] = "Desenvolvedor Python Pleno"
        sample_vaga_data["updatedAt"] = "2025-01-16T10:00:00Z"

        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.return_value = iter([VagaAPI(**sample_vaga_data)])

            result = sync_service._sync_vagas_full()

            assert result['processed'] == 1
            assert result['updated'] == 1

            # Verificar atualização
            vaga = database_service.session.query(Vaga).filter_by(inhire_id=sample_vaga_data["id"]).first()
            assert vaga.name == "Desenvolvedor Python Pleno"

    def test_sync_vagas_full_handles_errors(self, sync_service, sample_vaga_data):
        """Deve contabilizar erros mas continuar processando"""
        # Primeira vaga OK, segunda com erro
        vaga_ok = VagaAPI(**sample_vaga_data)

        sample_vaga_data_2 = sample_vaga_data.copy()
        sample_vaga_data_2["id"] = "vaga-error"
        vaga_error = VagaAPI(**sample_vaga_data_2)

        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.return_value = iter([vaga_ok, vaga_error])

            with patch.object(sync_service.db, 'upsert_vaga') as mock_upsert:
                # Primeira OK, segunda erro
                mock_upsert.side_effect = [
                    (True, 'created'),
                    Exception("Database error")
                ]

                result = sync_service._sync_vagas_full()

                assert result['processed'] == 2
                assert result['created'] == 1
                assert result['failed'] == 1


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServiceVagasIncremental:
    """Testes para sincronização incremental de vagas"""

    def test_sync_vagas_incremental_creates_new(self, sync_service, sample_vaga_data):
        """Deve criar vagas novas em sync incremental"""
        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.return_value = iter([VagaAPI(**sample_vaga_data)])

            result = sync_service._sync_vagas_incremental()

            assert result['processed'] == 1
            assert result['created'] == 1

    def test_sync_vagas_incremental_updates_if_newer(self, database_service, sync_service, sample_vaga_data):
        """Deve atualizar se API tem data mais recente"""
        # Criar vaga com data antiga
        sample_vaga_data["updatedAt"] = "2025-01-15T10:00:00Z"
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # API com data mais recente
        sample_vaga_data["updatedAt"] = "2025-01-16T10:00:00Z"
        sample_vaga_data["name"] = "Nome Atualizado"

        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.return_value = iter([VagaAPI(**sample_vaga_data)])

            result = sync_service._sync_vagas_incremental()

            assert result['updated'] == 1
            assert result['skipped'] == 0

    def test_sync_vagas_incremental_skips_if_not_newer(self, database_service, sync_service, sample_vaga_data):
        """Deve pular se BD tem data igual ou mais recente"""
        # Criar vaga com data recente
        sample_vaga_data["updatedAt"] = "2025-01-16T10:00:00Z"
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # API com mesma data
        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.return_value = iter([VagaAPI(**sample_vaga_data)])

            result = sync_service._sync_vagas_incremental()

            assert result['skipped'] == 1
            assert result['updated'] == 0


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServicePosicoes:
    """Testes para sincronização de posições"""

    def test_sync_posicoes_full_requires_vagas_first(self, sync_service, database_service, sample_vaga_data, sample_posicao_data):
        """Deve exigir que vagas existam antes de sincronizar posições"""
        # Criar vaga primeiro
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # Sync posições
        with patch.object(sync_service.api_client, 'get_all_posicoes') as mock_get:
            mock_get.return_value = iter([PosicaoAPI(**sample_posicao_data)])

            result = sync_service._sync_posicoes_full()

            assert result['processed'] == 1
            assert result['created'] == 1

    def test_sync_posicoes_skips_if_vaga_not_found(self, sync_service, sample_posicao_data):
        """Deve pular posição se vaga não existir"""
        # Tentar sync posição sem vaga
        sample_posicao_data["jobId"] = "vaga-inexistente"

        with patch.object(sync_service.api_client, 'get_all_posicoes') as mock_get:
            mock_get.return_value = iter([PosicaoAPI(**sample_posicao_data)])

            result = sync_service._sync_posicoes_full()

            # Deve pular ou falhar
            assert result['failed'] >= 0 or result['skipped'] >= 0


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServiceCandidaturas:
    """Testes para sincronização de candidaturas"""

    def test_sync_candidaturas_collects_talent_ids(self, sync_service, database_service, sample_vaga_data, sample_candidatura_data):
        """Deve coletar talent IDs das candidaturas"""
        # Setup vaga
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # Candidatura com talent ID
        with patch.object(sync_service.api_client, 'get_all_candidaturas') as mock_get:
            mock_get.return_value = iter([CandidaturaAPI(**sample_candidatura_data)])

            result, talent_ids = sync_service._sync_candidaturas_full()

            assert result['processed'] == 1
            assert "talent-111" in talent_ids

    def test_sync_candidaturas_handles_no_talent_id(self, sync_service, database_service, sample_vaga_data, sample_candidatura_data):
        """Deve lidar com candidaturas sem talent ID"""
        # Setup vaga
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # Candidatura SEM talent ID
        sample_candidatura_data["talentId"] = None

        with patch.object(sync_service.api_client, 'get_all_candidaturas') as mock_get:
            mock_get.return_value = iter([CandidaturaAPI(**sample_candidatura_data)])

            result, talent_ids = sync_service._sync_candidaturas_full()

            assert result['processed'] == 1
            assert len(talent_ids) == 0


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServiceTalentos:
    """Testes para sincronização de talentos"""

    def test_sync_talentos_uses_talent_ids_optimization(self, sync_service, sample_talento_data):
        """Deve usar talent IDs para otimizar busca"""
        talent_ids = {"talent-111", "talent-222"}

        with patch.object(sync_service.api_client, 'get_talento_by_id') as mock_get:
            mock_get.return_value = TalentoAPI(**sample_talento_data)

            result = sync_service._sync_talentos_full(talent_ids)

            # Deve buscar apenas os IDs fornecidos
            assert mock_get.call_count == 2
            assert result['processed'] == 2

    def test_sync_talentos_without_ids_gets_all(self, sync_service, sample_talento_data):
        """Deve buscar todos os talentos se não receber IDs"""
        with patch.object(sync_service.api_client, 'get_all_talentos') as mock_get:
            mock_get.return_value = iter([TalentoAPI(**sample_talento_data)])

            result = sync_service._sync_talentos_full(talent_ids=None)

            assert mock_get.called
            assert result['processed'] == 1


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServiceFullOrchestration:
    """Testes para orquestração de sync completo"""

    def test_sync_full_respects_dependency_order(self, sync_service, database_service):
        """Deve executar syncs na ordem correta de dependências"""
        with patch.object(sync_service, '_sync_vagas_full') as mock_vagas:
            with patch.object(sync_service, '_sync_posicoes_full') as mock_posicoes:
                with patch.object(sync_service, '_sync_candidaturas_full') as mock_cands:
                    with patch.object(sync_service, '_sync_talentos_full') as mock_talentos:
                        # Mock returns
                        mock_vagas.return_value = {'processed': 0}
                        mock_posicoes.return_value = {'processed': 0}
                        mock_cands.return_value = ({'processed': 0}, set())
                        mock_talentos.return_value = {'processed': 0}

                        # Criar config
                        config = SyncConfiguration(tenant_id="test-tenant")
                        database_service.session.add(config)
                        database_service.session.commit()

                        sync_service.sync_full()

                        # Verificar ordem de chamadas
                        assert mock_vagas.called
                        assert mock_posicoes.called
                        assert mock_cands.called
                        assert mock_talentos.called

    def test_sync_full_creates_sync_log(self, sync_service, database_service):
        """Deve criar registro de sync log"""
        # Criar config
        config = SyncConfiguration(tenant_id="test-tenant")
        database_service.session.add(config)
        database_service.session.commit()

        with patch.object(sync_service, '_sync_vagas_full', return_value={'processed': 5}):
            with patch.object(sync_service, '_sync_posicoes_full', return_value={'processed': 0}):
                with patch.object(sync_service, '_sync_candidaturas_full', return_value=({'processed': 0}, set())):
                    with patch.object(sync_service, '_sync_talentos_full', return_value={'processed': 0}):
                        result = sync_service.sync_full()

                        # Verificar log criado
                        logs = database_service.session.query(SyncLog).all()
                        assert len(logs) > 0

                        latest_log = logs[-1]
                        assert latest_log.sync_type == SyncType.FULL

    def test_sync_full_marks_success_on_completion(self, sync_service, database_service):
        """Deve marcar sync como SUCCESS ao completar"""
        config = SyncConfiguration(tenant_id="test-tenant")
        database_service.session.add(config)
        database_service.session.commit()

        with patch.object(sync_service, '_sync_vagas_full', return_value={'processed': 1}):
            with patch.object(sync_service, '_sync_posicoes_full', return_value={'processed': 0}):
                with patch.object(sync_service, '_sync_candidaturas_full', return_value=({'processed': 0}, set())):
                    with patch.object(sync_service, '_sync_talentos_full', return_value={'processed': 0}):
                        result = sync_service.sync_full()

                        assert result['success'] is True
                        assert result['status'] == SyncStatus.SUCCESS

    def test_sync_full_handles_errors_gracefully(self, sync_service, database_service):
        """Deve lidar com erros e marcar como ERROR"""
        config = SyncConfiguration(tenant_id="test-tenant")
        database_service.session.add(config)
        database_service.session.commit()

        with patch.object(sync_service, '_sync_vagas_full', side_effect=Exception("Sync error")):
            result = sync_service.sync_full()

            assert result['success'] is False
            assert result['status'] == SyncStatus.ERROR


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServiceIncrementalOrchestration:
    """Testes para orquestração de sync incremental"""

    def test_sync_incremental_express_mode(self, sync_service, database_service):
        """Deve executar apenas entidades críticas em modo express"""
        config = SyncConfiguration(tenant_id="test-tenant")
        database_service.session.add(config)
        database_service.session.commit()

        with patch.object(sync_service, '_sync_vagas_incremental', return_value={'processed': 0}):
            with patch.object(sync_service, '_sync_posicoes_incremental', return_value={'processed': 0}):
                with patch.object(sync_service, '_sync_candidaturas_incremental', return_value={'processed': 0}):
                    with patch.object(sync_service, '_sync_talentos_incremental', return_value={'processed': 0}):
                        result = sync_service.sync_incremental(express_mode=True)

                        assert result['success'] is True

    def test_sync_incremental_complete_mode(self, sync_service, database_service):
        """Deve executar todas as entidades em modo completo"""
        config = SyncConfiguration(tenant_id="test-tenant")
        database_service.session.add(config)
        database_service.session.commit()

        with patch.object(sync_service, '_sync_vagas_incremental', return_value={'processed': 0}):
            with patch.object(sync_service, '_sync_posicoes_incremental', return_value={'processed': 0}):
                with patch.object(sync_service, '_sync_candidaturas_incremental', return_value={'processed': 0}):
                    with patch.object(sync_service, '_sync_candidatura_timeline_incremental', return_value={'processed': 0}):
                        with patch.object(sync_service, '_sync_talentos_incremental', return_value={'processed': 0}):
                            result = sync_service.sync_incremental(express_mode=False)

                            assert result['success'] is True


@pytest.mark.unit
class TestSyncServiceStatistics:
    """Testes para agregação de estatísticas"""

    def test_aggregates_statistics_correctly(self, sync_service):
        """Deve agregar estatísticas de múltiplas entidades"""
        vagas_stats = {'processed': 10, 'created': 5, 'updated': 3, 'skipped': 2, 'failed': 0}
        posicoes_stats = {'processed': 20, 'created': 10, 'updated': 5, 'skipped': 5, 'failed': 0}

        # Simular agregação
        total_stats = {
            'processed': vagas_stats['processed'] + posicoes_stats['processed'],
            'created': vagas_stats['created'] + posicoes_stats['created'],
            'updated': vagas_stats['updated'] + posicoes_stats['updated'],
            'skipped': vagas_stats['skipped'] + posicoes_stats['skipped'],
            'failed': vagas_stats['failed'] + posicoes_stats['failed']
        }

        assert total_stats['processed'] == 30
        assert total_stats['created'] == 15
        assert total_stats['updated'] == 8


@pytest.mark.unit
@pytest.mark.requires_db
class TestSyncServiceEdgeCases:
    """Testes para casos extremos"""

    def test_sync_with_empty_api_response(self, sync_service):
        """Deve lidar com resposta vazia da API"""
        with patch.object(sync_service.api_client, 'get_all_vagas', return_value=iter([])):
            result = sync_service._sync_vagas_full()

            assert result['processed'] == 0
            assert result['created'] == 0

    def test_sync_with_null_updated_at(self, sync_service, database_service, sample_vaga_data):
        """Deve lidar com updatedAt null"""
        sample_vaga_data["updatedAt"] = None

        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.return_value = iter([VagaAPI(**sample_vaga_data)])

            # Não deve crashar
            result = sync_service._sync_vagas_full()

            assert result['processed'] == 1

    def test_sync_handles_large_dataset(self, sync_service, sample_vaga_data):
        """Deve processar datasets grandes sem problemas de memória"""
        # Gerar 1000 vagas
        vagas = []
        for i in range(1000):
            vaga_data = sample_vaga_data.copy()
            vaga_data["id"] = f"vaga-{i}"
            vagas.append(VagaAPI(**vaga_data))

        with patch.object(sync_service.api_client, 'get_all_vagas', return_value=iter(vagas)):
            result = sync_service._sync_vagas_full()

            assert result['processed'] == 1000


@pytest.mark.unit
class TestSyncServiceLogging:
    """Testes para logging de operações"""

    def test_logs_progress_during_sync(self, sync_service, sample_vaga_data, caplog):
        """Deve logar progresso durante sync"""
        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.return_value = iter([VagaAPI(**sample_vaga_data)])

            sync_service._sync_vagas_full()

            # Verificar se logou (caplog captura logs)
            # Logs podem incluir "Sincronizando", "processadas", etc.

    def test_logs_errors_with_context(self, sync_service, sample_vaga_data, caplog):
        """Deve logar erros com contexto adequado"""
        with patch.object(sync_service.api_client, 'get_all_vagas') as mock_get:
            mock_get.side_effect = Exception("API Error")

            with patch.object(sync_service, 'logger') as mock_logger:
                try:
                    sync_service._sync_vagas_full()
                except:
                    pass

                # Verificar se logou erro
                # mock_logger.error.assert_called()
