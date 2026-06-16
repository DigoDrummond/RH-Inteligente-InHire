# Estrutura do Projeto InHire

## Visão Geral

Sistema de sincronização de dados entre a API InHire e banco de dados PostgreSQL local.

## Estrutura de Diretórios

```
Inhire/
│
├── config.py                          # Configurações do sistema
├── run_sync.py                        # Script principal de sincronização
├── scheduler.py                       # Agendador de tarefas
├── init_database.py                   # Inicialização do banco de dados
├── metrics_server.py                  # Servidor de métricas
│
├── models/                            # Modelos de dados (SQLAlchemy)
│   └── database.py                    # Definição de todas as tabelas
│
├── services/                          # Camada de serviços
│   ├── api_client.py                  # Cliente da API InHire
│   ├── auth_service.py                # Autenticação com InHire
│   ├── database_service.py            # Operações de banco de dados
│   └── sync_service.py                # Lógica de sincronização
│
├── utils/                             # Utilitários
│   ├── logger.py                      # Configuração de logs
│   └── retry.py                       # Decoradores de retry
│
├── scripts/                           # Scripts auxiliares
│   ├── diagnostics/                   # Scripts de diagnóstico
│   ├── maintenance/                   # Scripts de manutenção
│   ├── sql/                          # Scripts SQL
│   └── examples/                      # Exemplos de uso
│
├── tests/                             # Testes automatizados
│   ├── conftest.py                    # Configuração do pytest
│   ├── test_database_service.py
│   ├── test_declined_candidates_service.py
│   ├── test_api_vagas.py
│   ├── test_upsert_candidatura.py
│   ├── test_sync_incremental_demo.py
│   └── test_scheduler.py
│
├── docs/                              # Documentação
│   ├── PROJECT_STRUCTURE.md           # Este arquivo
│   ├── TROUBLESHOOTING_ENUM_DECLINED.md
│   ├── ARQUITETURA_SISTEMA_INTEGRADO.md
│   └── GUIA_3_TIPOS_SYNC.md
│
├── logs/                              # Arquivos de log
│   └── inhire_sync.log
│
└── database_backups/                  # Backups do banco de dados
```

## Componentes Principais

### Modelos (`models/`)

Define a estrutura do banco de dados usando SQLAlchemy ORM:

- **Vagas**: Jobs/posições abertas
- **Posições**: Instâncias específicas de vagas
- **Candidaturas**: Aplicações de talentos em vagas
- **Talentos**: Perfis de candidatos
- **CandidaturaTimeline**: Histórico de mudanças de status
- **SyncLog**: Logs de sincronizações
- **SyncConfiguration**: Configurações por tenant

### Serviços (`services/`)

#### `api_client.py`
Cliente HTTP para a API InHire com:
- Paginação automática
- Retry com backoff exponencial
- Rate limiting
- Autenticação via OAuth2

#### `auth_service.py`
Gerenciamento de autenticação:
- Login com credenciais
- Refresh de tokens
- Armazenamento seguro de tokens

#### `database_service.py`
Operações de banco de dados:
- CRUD para todas as entidades
- Upsert (insert ou update)
- Transações
- Bulk operations

#### `sync_service.py`
Orquestração da sincronização:
- Sincronização completa
- Sincronização incremental
- Sincronização por entidade
- Gestão de erros e retry

### Scripts (`scripts/`)

Ver [scripts/README.md](../scripts/README.md) para detalhes completos.

### Testes (`tests/`)

Testes automatizados usando pytest:
- Testes unitários de serviços
- Testes de integração com banco
- Mocks para chamadas API
- Fixtures para dados de teste

## Fluxo de Dados

```
API InHire
    ↓
api_client.py (fetch)
    ↓
sync_service.py (transform)
    ↓
database_service.py (upsert)
    ↓
PostgreSQL Database
```

## Configuração

### Variáveis de Ambiente

Definidas em `config.py` via `.env` ou variáveis de sistema:

```
# InHire API
INHIRE_API_BASE_URL=https://api.inhire.app
INHIRE_CLIENT_ID=your_client_id
INHIRE_CLIENT_SECRET=your_secret

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=inhire
DB_USER=postgres
DB_PASSWORD=your_password

# Sync
SYNC_BATCH_SIZE=50
SYNC_ENABLED=true
```

## Sincronização

### Tipos de Sincronização

1. **Completa (`--full`)**
   - Sincroniza todos os dados
   - ~104.558 registros
   - Duração: ~55 minutos

2. **Incremental (`--incremental`)**
   - Apenas dados novos/modificados
   - Baseada em `updated_at`
   - Duração: ~2-5 minutos

3. **Por Entidade**
   - Sincroniza apenas uma entidade
   - Útil para correções pontuais

### Execução

```bash
# Sincronização completa
python run_sync.py --full

# Sincronização incremental
python run_sync.py --incremental
```

## Logs

Logs estruturados em JSON em `logs/inhire_sync.log`:

```json
{
  "timestamp": "2025-11-19T12:03:46.464969",
  "level": "INFO",
  "logger": "services.sync_service",
  "message": "Vagas processadas: 1000",
  "pid": 3400,
  "environment": "production"
}
```

## Métricas

Servidor de métricas em `http://localhost:8000`:

- Total de sincronizações
- Tempo médio de sincronização
- Taxa de erro
- Registros processados por minuto

## Manutenção

### Backup do Banco

```bash
pg_dump -U postgres inhire > database_backups/inhire_backup_$(date +%Y%m%d).sql
```

### Limpeza de Logs

```bash
# Manter últimos 30 dias
find logs/ -name "*.log.*" -mtime +30 -delete
```

### Verificação de Saúde

```bash
python scripts/diagnostics/check_enum_detailed.py
python scripts/diagnostics/check_vaga_status.py
```

## Problemas Comuns

Ver [docs/TROUBLESHOOTING_ENUM_DECLINED.md](TROUBLESHOOTING_ENUM_DECLINED.md) e outras documentações em `docs/`.

## Contribuindo

1. Crie scripts de diagnóstico em `scripts/diagnostics/`
2. Scripts de correção em `scripts/maintenance/`
3. Migrações SQL em `scripts/sql/migrations/`
4. Adicione testes em `tests/`
5. Documente em `docs/`

## Licença

Proprietary - Uso interno apenas
