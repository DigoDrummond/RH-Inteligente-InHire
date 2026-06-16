# Guia Rápido - Novas Funcionalidades

## Instalação

```bash
# 1. Instalar novas dependências
pip install -r requirements.txt
```

## 1. Análise de Candidatos Declined

### Uso Básico

```bash
# Executar análise interativa completa
python scripts/utilities/analyze_declined_candidates.py
```

### Uso Programático

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.declined_candidates_service import DeclinedCandidatesService

# Criar sessão
engine = create_engine("postgresql://user:pass@localhost/inhire_sync")
Session = sessionmaker(bind=engine)
session = Session()

# Inicializar serviço
service = DeclinedCandidatesService(session)

# Buscar candidatos declined
declined = service.get_declined_candidates(days_ago=30)

# Ver estatísticas
stats = service.get_declined_stats_by_job()

# Calcular taxas de declínio
rates = service.get_declined_rate_by_job()

# Análise de padrões
patterns = service.get_declined_reasons_analysis()

# Exportar relatório
csv_path = service.export_declined_report()
```

## 2. Executar Testes

### Todos os testes

```bash
pytest tests/ -v
```

### Com cobertura

```bash
pytest tests/ --cov --cov-report=term-missing
```

### Usando script

```bash
python scripts/utilities/run_tests.py
```

### Testes específicos

```bash
# Apenas testes do DatabaseService
pytest tests/test_database_service.py -v

# Apenas testes do DeclinedCandidatesService
pytest tests/test_declined_candidates_service.py -v
```

## 3. Métricas Prometheus

### Iniciar servidor

```bash
python metrics_server.py
```

Acesse: http://localhost:8000/metrics

### Usar em código

```python
from utils.metrics import (
    track_sync_duration,
    record_sync_stats,
    MetricsContext
)

# Decorator
@track_sync_duration('vaga', 'full')
def sync_vagas():
    # Seu código aqui
    pass

# Context manager
with MetricsContext('vaga', 'full') as ctx:
    # Seu código de sincronização
    stats = {'created': 10, 'updated': 5, 'skipped': 2, 'failed': 0}
    ctx.record_stats(stats)

# Função direta
record_sync_stats('vaga', {'created': 10, 'updated': 5})
```

### Integrar com Prometheus

1. **Instalar Prometheus**: https://prometheus.io/download/

2. **Configurar** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'inhire_sync'
    static_configs:
      - targets: ['localhost:8000']
```

3. **Iniciar Prometheus**:
```bash
./prometheus --config.file=prometheus.yml
```

4. **Acessar**: http://localhost:9090

## 4. Configuração

Adicione ao `.env`:

```env
# Métricas
METRICS_ENABLED=true
METRICS_PORT=8000
METRICS_UPDATE_INTERVAL_SECONDS=30
```

## 5. Exemplos de Queries Prometheus

```promql
# Taxa de sucesso de sincronizações (últimas 24h)
rate(inhire_sync_executions_total{status="success"}[24h])

# Tempo médio de sincronização por entidade
rate(inhire_sync_duration_seconds_sum[5m]) / rate(inhire_sync_duration_seconds_count[5m])

# Total de candidatos declined
inhire_declined_candidates_total

# Taxa de erro da API
rate(inhire_api_errors_total[5m])
```

## 6. Dashboards Grafana

### Métricas Principais

- **Sync Duration**: `inhire_sync_duration_seconds`
- **Records Processed**: `inhire_sync_records_total`
- **API Response Time**: `inhire_api_request_duration_seconds`
- **Declined Rate**: `inhire_declined_rate_by_job`
- **Database Size**: `inhire_database_records_count`

### Alertas Sugeridos

1. **Taxa de erro > 5%**
2. **Tempo de sync > 10 minutos**
3. **API response time > 5 segundos**
4. **Decline rate > 30% em uma vaga**

## 7. Troubleshooting

### Testes falhando

```bash
# Limpar cache e rodar novamente
pytest --cache-clear tests/ -v

# Ver output detalhado
pytest tests/ -vv -s
```

### Servidor de métricas não inicia

```bash
# Verificar se porta está disponível
netstat -an | grep 8000

# Ou usar porta diferente
METRICS_PORT=8001 python metrics_server.py
```

### Cobertura baixa

```bash
# Ver relatório detalhado
pytest --cov --cov-report=html
# Abrir htmlcov/index.html no navegador
```

## 8. Documentação Completa

Ver: `docs/MELHORIAS_2025-11-13.md`

## 9. Estrutura de Arquivos Criados

```
services/
└── declined_candidates_service.py

scripts/utilities/
├── analyze_declined_candidates.py
└── run_tests.py

tests/
├── __init__.py
├── conftest.py
├── test_database_service.py
└── test_declined_candidates_service.py

utils/
└── metrics.py

docs/
└── MELHORIAS_2025-11-13.md

metrics_server.py
pytest.ini
QUICK_START_MELHORIAS.md
```

## 10. Checklist de Verificação

- [ ] Dependências instaladas: `pip install -r requirements.txt`
- [ ] Testes passando: `pytest tests/ -v`
- [ ] Servidor de métricas funcional: `python metrics_server.py`
- [ ] Análise de declined funcional: `python scripts/utilities/analyze_declined_candidates.py`
- [ ] Configurações em `.env` atualizadas

---

**Pronto para usar!** 🚀
