# Sistema de Sincronização Inhire → PostgreSQL

Sistema completo em Python para sincronização automática de dados entre a plataforma Inhire e banco de dados PostgreSQL, com exportação para Google Sheets e notificações via webhooks.

**Última atualização:** 2026-08-21
**Status:** ✅ Produção - Reorganização Completa

---

## 📚 Documentação Completa

**IMPORTANTE:** Consulte sempre o arquivo principal de documentação:
- **[docs/CLAUDE.md](docs/CLAUDE.md)** - Documentação master do projeto (configuração, rotinas, troubleshooting)
- **[docs/README.md](docs/README.md)** - Índice completo da documentação
- **[docs/guides/ROTINAS_AGENDAMENTO.md](docs/guides/ROTINAS_AGENDAMENTO.md)** - Guia técnico das rotinas
- **[docs/guides/GUIA_CONFIGURACAO_AGENDADOR_WINDOWS.md](docs/guides/GUIA_CONFIGURACAO_AGENDADOR_WINDOWS.md)** - Setup Windows Task Scheduler

---

## 🚀 Quick Start

### Instalação

```bash
# 1. Clonar repositório
git clone <repo-url>
cd Inhire

# 2. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env com suas credenciais
```

### Primeira Execução

```bash
# 1. Inicializar banco de dados
python init_database.py

# 2. Sincronização completa (primeira vez - obrigatório)
python run_sync.py --full

# 3. Sincronização incremental (uso diário)
python sync_incremental_completo.py --completa
```

---

## 📊 Sincronização de Dados

### Tipos de Sincronização

| Modo | Duração | Cobertura | Quando Usar |
|------|---------|-----------|-------------|
| **FULL** | 55 min | 100% | 1ª execução, 1x/semana |
| **INCREMENTAL** | 40-50 min | 100% | Manutenção, 1-2x/dia |

### Comandos

```bash
# Sync completa (todas as entidades, todos os dados)
python run_sync.py --full

# Sync incremental (apenas dados modificados)
python sync_incremental_completo.py --completa --yes

# Sync de talent pool (talentos sem candidaturas)
python scripts/sync/sync_talent_pool.py
```

---

## 📤 Exportação para Google Sheets

### Scripts Disponíveis

```bash
# Exportar análise de posições (1.383 registros)
python scripts/export/export_analise_posicoes.py

# Exportar candidaturas (35k+ registros)
python scripts/export/export_relatorio_candidaturas.py

# Exportar dados Jade (customizados)
python scripts/export/export_dados_jade.py

# Exportar funil de performance (85k+ registros)
python scripts/export/export_funil_performance.py
```

### Autenticação OAuth2

- Arquivos necessários: `credentials.json`, `token.pickle`
- Primeira execução abre navegador para autenticação
- Token salvo automaticamente para reuso

---

## 🤖 Rotinas Agendadas (Windows Task Scheduler)

### Rotinas Diárias

**Arquivo:** `rotinas/rotina_diaria.bat`
**Frequência:** Segunda a Sábado, 08:00 e 20:00
**Duração:** ~50 minutos
**Executa:**
1. Sync Incremental (~45 min)
2. Export Sheets Principal
3. Export Análise Posições
4. Export Dados Jade
5. Export Candidaturas (com webhook)

### Rotina Semanal

**Arquivo:** `rotinas/rotina_semanal.bat`
**Frequência:** Domingo 02:00
**Duração:** ~70 minutos
**Executa:**
1. Backup BD (~10 min)
2. Sync FULL (~55 min)
3. Export Sheets (~5 min)

### Configuração

Consulte: [docs/guides/GUIA_CONFIGURACAO_AGENDADOR_WINDOWS.md](docs/guides/GUIA_CONFIGURACAO_AGENDADOR_WINDOWS.md)

---

## 📁 Estrutura do Projeto (Reorganizada em 2026-08-21)

```
Inhire/
├── 📄 Raiz (arquivos essenciais)
│   ├── config.py                     # Configurações centralizadas
│   ├── run_sync.py                   # Sync completa
│   ├── sync_incremental_completo.py  # Sync incremental
│   ├── scheduler.py                  # Agendador Python (alternativa)
│   ├── health_check.py               # Verificação de saúde
│   ├── init_database.py              # Inicialização do BD
│   ├── requirements.txt              # Dependências Python
│   ├── .env                          # Credenciais (não versionado)
│   ├── .gitignore                    # Arquivos ignorados
│   └── README.md                     # Este arquivo
│
├── 📂 models/                        # Modelos SQLAlchemy
│   ├── database.py                   # Definições de tabelas
│   └── api_schemas.py                # Schemas da API Inhire
│
├── 📂 services/                      # Serviços de negócio
│   ├── auth_service.py               # Autenticação JWT
│   ├── api_client.py                 # Cliente HTTP API Inhire
│   ├── database_service.py           # Operações banco de dados
│   └── sync_service.py               # Orquestrador de sincronização
│
├── 📂 repositories/                  # Repositórios de dados
├── 📂 interfaces/                    # Interfaces (contratos)
├── 📂 utils/                         # Utilitários
│   ├── logger.py                     # Sistema de logs
│   ├── rate_limiter.py               # Rate limiting
│   └── retry.py                      # Mecanismo de retry
│
├── 📂 scripts/                       # Scripts utilitários
│   ├── export/                       # Exportação Google Sheets
│   ├── sync/                         # Sincronizações especiais
│   ├── webhooks/                     # Notificações Google Chat
│   ├── migration/                    # Execução de migrations
│   ├── monitoring/                   # Monitoramento (Prometheus)
│   ├── analise/                      # Análises de dados
│   ├── backup/                       # Scripts de backup
│   ├── cleanup/                      # Limpeza e manutenção
│   ├── validacao/                    # Validações
│   └── debug/                        # Debug (vazio em produção)
│       └── archive_2026-08/          # Scripts debug arquivados (80)
│
├── 📂 migrations/                    # Migrations SQL
│   ├── 060-084_*.sql                 # Migrations ativas (32)
│   ├── applied_2024-2025/            # Migrations antigas (59)
│   └── obsolete_iterations/          # Migrations obsoletas (20)
│
├── 📂 rotinas/                       # Scripts .BAT agendados (11)
│   ├── rotina_diaria.bat             # Rotina diária mestra
│   ├── rotina_semanal.bat            # Rotina semanal mestra
│   ├── sync_*.bat                    # Sincronizações
│   ├── export_*.bat                  # Exportações
│   ├── backup_bd.bat                 # Backup PostgreSQL
│   └── health_check.bat              # Health check
│
├── 📂 docs/                          # Documentação completa
│   ├── CLAUDE.md                     # Documentação MASTER
│   ├── README_SYNC.md                # Guia de sincronização
│   ├── guides/                       # Guias práticos (4)
│   ├── reports/                      # Relatórios técnicos (3)
│   └── analysis/                     # Análises técnicas (5)
│
├── 📂 logs/                          # Logs do sistema
├── 📂 tests/                         # Testes pytest
├── 📂 webhooks/                      # Webhooks Google Apps Script
├── 📂 data_science/                  # Projeto data science (separado)
└── 📂 archive_legacy/                # Diretórios legacy arquivados (7)
    ├── analise_inhire/               # Análises antigas
    ├── apps_script/                  # Scripts Apps Script antigos
    ├── apps_script_webapp/           # Webapp antiga
    ├── campos_personalizados/        # Custom fields antigos
    ├── exports_analise/              # Exports antigos
    ├── monitoring/                   # Monitoring antigo
    └── reports/                      # Reports antigos
```

---

## 🗄️ Banco de Dados

### Conexão

```
Host: localhost
Porta: 5432
Database: inhire
User: postgres
Schema: public
```

### Tabelas Principais

- `vagas` - Vagas abertas e fechadas
- `posicoes` - Posições dentro de vagas
- `position_timeline` - Histórico de mudanças
- `candidaturas` - Candidaturas de talentos
- `talentos` - Candidatos/profissionais
- `requisicoes` - Aprovações de requisições
- `clientes` - Clientes do tenant

### Views de Análise

- `vw_analise_posicoes` - Análise completa de posições (1.383 registros)
- `vw_relatorio_candidaturas` - Relatório de candidaturas (35k+ registros)
- `vw_funil_performance` - Funil de candidaturas (85k+ registros)
- `vw_dados_jade` - Dados customizados

---

## 🔧 Configuração (.env)

```env
# API Inhire
INHIRE_TENANT=frameworkdigital
INHIRE_SERVICE_ACCOUNT=service-account-xxx@inhire.app
INHIRE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=inhire
DB_USER=postgres
DB_PASSWORD=[senha]

# Google Sheets (OAuth2)
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEETS_TOKEN_FILE=token.pickle

# Rate Limiting
INHIRE_MAX_REQUESTS_PER_MINUTE=200
```

---

## 📊 Monitoramento

### Logs

```bash
# Ver logs de sincronização
tail -f logs/inhire_sync.log

# Ver logs de exportação
tail -f logs/export_candidaturas.log

# Ver logs de rotinas agendadas
tail -f logs/rotinas.log
```

### Queries SQL Úteis

```sql
-- Ver últimas sincronizações
SELECT sync_type, sync_entity, status, start_time, records_processed
FROM sync_log
ORDER BY start_time DESC
LIMIT 10;

-- Ver tabelas desatualizadas
SELECT 'vagas' as tabela, MAX(updated_at_inhire) as ultima_sync,
       NOW() - MAX(updated_at_inhire) as tempo_desde_sync
FROM vagas;
```

---

## ⚠️ Limitações Conhecidas

### Talent Pool (72,4% de cobertura)

- **Problema:** API `/talents/paginated` retorna apenas ~473 talentos
- **Impacto:** ~23.533 talentos SEM candidaturas não sincronizados
- **Workaround:** Script `sync_talent_pool.py` semanal
- **Solução:** Aguardando suporte Inhire para endpoint completo
- **Detalhes:** Ver [docs/CLAUDE.md](docs/CLAUDE.md) seção "Limitação Talent Pool"

---

## 🚨 Troubleshooting

### Erro: "Nenhuma sincronização anterior encontrada"
```bash
# Executar sync FULL primeiro
python run_sync.py --full
```

### Erro: "Timeout ao buscar dados"
```bash
# Aumentar timeout no .env
SYNC_INCREMENTAL_TIMEOUT_READ=180
```

### Sync muito lenta (>60min)
```bash
# Ver relatório de tempo por tabela
# Verificar skip rate (deve ser >70%)
# Se persistir, executar sync FULL
python run_sync.py --full
```

---

## 📞 Suporte

1. **Documentação Master:** [docs/CLAUDE.md](docs/CLAUDE.md)
2. **Guias Práticos:** [docs/guides/](docs/guides/)
3. **Relatórios:** [docs/reports/](docs/reports/)
4. **Logs:** `logs/inhire_sync.log`

---

## 📝 Changelog Recente

**2026-08-21** - Reorganização Completa do Projeto
- ✅ 80 scripts de debug arquivados
- ✅ 7 diretórios legacy arquivados
- ✅ 79 migrations antigas organizadas
- ✅ 13 documentos reorganizados
- ✅ READMEs criados para todas as pastas
- ✅ .gitignore atualizado
- ✅ Estrutura validada (imports OK)

**2026-03-04** - Validação de Performance
- ✅ Duração real de sync incremental: 40-50 minutos
- ✅ Relatório de TEMPO POR TABELA implementado
- ✅ 100% de consistência mantida

**2026-03-02** - Correção Crítica
- ✅ Removida otimização que causava perda de dados
- ✅ 100% de consistência garantida
- ⚠️ Sync incremental mais lenta (trade-off aceito)

---

**Versão:** 2.3 (Reorganização Completa)
**Mantido por:** Framework Digital
**Python:** 3.10+
**PostgreSQL:** 18
**Licença:** Uso interno
