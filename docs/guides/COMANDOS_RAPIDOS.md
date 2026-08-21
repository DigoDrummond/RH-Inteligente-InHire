# Comandos Rápidos - Sincronização e Exportação

**Última atualização:** 2026-03-10
**Versão:** 2.0 (Atualizado com exportação Google Sheets)

---

## Sincronização com API Inhire

### 1. Sincronização Incremental Completa (RECOMENDADO)

```bash
python sync_incremental_completo.py --completa --yes
```

**Características:**
- Cobertura: 100% de todas as tabelas (11 entidades)
- Duração: 15-25 minutos
- Modo: Automático (sem confirmação)
- Quando usar: Rotina diária (1-2x/dia)

**Entidades sincronizadas:**
- Vagas
- Posições
- **Position Timeline** (correção aplicada em 10/03/2026)
- Candidaturas
- Candidatura Timeline
- Vaga Tags
- Requisições
- Talentos
- Clientes
- Scorecard Interviews
- Scorecard Jobs

**Com confirmação manual:**
```bash
python sync_incremental_completo.py --completa
```

---

### 2. Sincronização Completa (Full)

```bash
python run_sync.py --full
```

**Características:**
- Cobertura: 100%
- Duração: 55-60 minutos
- Quando usar: Primeira vez ou semanal (domingos)

---

## Exportação para Google Sheets

### 1. Exportar vw_analise_posicoes

```bash
python scripts/export/export_analise_posicoes.py
```

**Destino:**
- Planilha: https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw
- Aba: **Teste_API**
- Registros: ~1.410 × 34 colunas
- Método: OAuth2

---

### 2. Exportar vw_funil_performance

```bash
python scripts/export/export_funil_performance.py
```

**Destino:**
- Planilha: https://docs.google.com/spreadsheets/d/1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0
- Aba: Funil_API
- Registros: ~85.000+ linhas

---

### 3. Exportar vw_dados_jade

```bash
python scripts/export/export_dados_jade.py
```

**Destino:**
- Planilha: https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw
- Aba: API_Dados_Jade
- Registros: ~689 linhas

---

## Sincronização + Exportação em Sequência

### Windows (Comando Único)

```cmd
python sync_incremental_completo.py --completa --yes && python scripts/export/export_analise_posicoes.py
```

**Duração total:** ~16-26 minutos (15-25 sync + 10-20s export)

---

### Windows: Script Batch (.bat)

**Criar arquivo:** `sync_and_export.bat`

```batch
@echo off
echo ================================================================================
echo  SINCRONIZACAO INCREMENTAL + EXPORTACAO GOOGLE SHEETS
echo ================================================================================
echo.

echo [1/2] Executando sincronizacao incremental completa...
echo.
python sync_incremental_completo.py --completa --yes

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Sincronizacao falhou! Exportacao cancelada.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo [2/2] Exportando vw_analise_posicoes para Google Sheets...
echo ================================================================================
echo.
python scripts\export\export_analise_posicoes.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Exportacao falhou!
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo  PROCESSO CONCLUIDO COM SUCESSO!
echo ================================================================================
echo.
pause
```

**Executar:**
```cmd
sync_and_export.bat
```

---

## Verificar Status da Sincronização

### Ver últimas sincronizações

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -t -A -c "SELECT sync_type, sync_entity, status, start_time AT TIME ZONE 'America/Sao_Paulo' as inicio, end_time AT TIME ZONE 'America/Sao_Paulo' as fim, EXTRACT(EPOCH FROM (end_time - start_time))/60 as duracao_min, records_processed FROM sync_log WHERE sync_type = 'INCREMENTAL' ORDER BY start_time DESC LIMIT 10;"
```

---

### Contar registros nas views

```bash
# vw_analise_posicoes
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -t -A -c "SELECT COUNT(*) FROM vw_analise_posicoes;"

# vw_funil_performance
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -t -A -c "SELECT COUNT(*) FROM vw_funil_performance;"
```

---

### Última atualização de position_timeline

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -t -A -c "SELECT MAX(updated_at) FROM position_timeline WHERE updated_at >= NOW() - INTERVAL '2 hours';"
```

---

## Agendamento Automático

### Frequência Recomendada

| Tipo | Frequência | Horário | Duração |
|------|------------|---------|---------|
| **Sync Incremental** | 1-2x/dia | 08:00, 20:00 | 15-25 min |
| **Sync Full** | 1x/semana | Domingo 02:00 | 55-60 min |
| **Exportação** | Após sync | 08:30, 20:30 | 10-20 seg |

---

### Windows: Script Agendador Python

**Criar arquivo:** `scheduler_auto.py`

```python
from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess

scheduler = BlockingScheduler(timezone="America/Sao_Paulo")

def run_sync_incremental():
    print("[SCHEDULER] Iniciando sincronização incremental...")
    subprocess.run(["python", "sync_incremental_completo.py", "--completa", "--yes"])

def run_export():
    print("[SCHEDULER] Iniciando exportação...")
    subprocess.run(["python", "scripts/export/export_analise_posicoes.py"])

def run_sync_full():
    print("[SCHEDULER] Iniciando sincronização completa...")
    subprocess.run(["python", "run_sync.py", "--full"])

# Sync incremental: 08:00 e 20:00
scheduler.add_job(run_sync_incremental, 'cron', hour='8,20', minute=0)

# Exportação: 08:30 e 20:30
scheduler.add_job(run_export, 'cron', hour='8,20', minute=30)

# Sync completa: Domingo 02:00
scheduler.add_job(run_sync_full, 'cron', day_of_week='sun', hour=2, minute=0)

print("Scheduler iniciado!")
print("Tarefas agendadas:")
print("  - Sync incremental: 08:00, 20:00")
print("  - Exportação: 08:30, 20:30")
print("  - Sync completa: Domingo 02:00")
print("\nPressione Ctrl+C para parar.")

scheduler.start()
```

**Executar:**
```bash
python scheduler_auto.py
```

**Instalar dependência:**
```bash
pip install apscheduler
```

---

## Troubleshooting

### Erro: "Nenhuma sincronização anterior encontrada"

**Solução:** Execute sync completa primeiro
```bash
python run_sync.py --full
```

---

### Erro: "Token expirado" (Google Sheets)

**Solução:** Deletar token e reautenticar
```cmd
del token.pickle
python scripts\export\export_analise_posicoes.py
```

**Nota:** Navegador abrirá para autenticação OAuth2

---

### Erro: "Falha na conexão com API"

**Verificar credenciais:**
```cmd
type .env | findstr INHIRE_
```

**Testar autenticação:**
```bash
python -c "from services.api_client import InhireAPIClient; InhireAPIClient().authenticate()"
```

---

### Sincronização muito lenta (>30 min)

**Ver progresso:**
```cmd
powershell "Get-Content logs\inhire_sync.log | Select-Object -Last 30"
```

**Ver estatísticas:**
```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "SELECT sync_entity, ROUND(EXTRACT(EPOCH FROM (end_time - start_time))/60, 2) as duracao_min FROM sync_log WHERE sync_type = 'INCREMENTAL' ORDER BY start_time DESC LIMIT 10;"
```

---

### Exportação falha com "Quota exceeded"

**Solução:** Aguardar rate limit (Google Sheets API: 100 req/100s)

---

## Referências Rápidas

### Planilhas Google Sheets

**1. Análise de Posições:**
- URL: https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw
- ID: `1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw`
- Abas: `Teste_API` (vw_analise_posicoes), `API_Dados_Jade` (vw_dados_jade)

**2. Funil de Performance:**
- URL: https://docs.google.com/spreadsheets/d/1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0
- ID: `1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0`
- Aba: `Funil_API` (vw_funil_performance)

---

### Arquivos de Configuração

| Arquivo | Descrição |
|---------|-----------|
| `.env` | Variáveis de ambiente (API, BD, Google) |
| `credentials.json` | Credenciais Google OAuth2 |
| `token.pickle` | Token OAuth2 em cache |
| `config.py` | Configurações do sistema |

---

### Scripts Principais

| Script | Descrição | Duração |
|--------|-----------|---------|
| `sync_incremental_completo.py` | Sync incremental 100% | 15-25 min |
| `run_sync.py --full` | Sync completa (full) | 55-60 min |
| `scripts/export/export_analise_posicoes.py` | Exporta vw_analise_posicoes | 10-20s |
| `scripts/export/export_funil_performance.py` | Exporta vw_funil_performance | 30-60s |
| `scripts/export/export_dados_jade.py` | Exporta vw_dados_jade | 5-10s |

---

## Logs e Monitoramento

### Ver últimas 50 linhas do log

```cmd
powershell "Get-Content logs\inhire_sync.log | Select-Object -Last 50"
```

---

### Filtrar erros

```cmd
powershell "Get-Content logs\inhire_sync.log | Select-String -Pattern 'ERROR'"
```

---

### Verificar modificação do token OAuth2

```cmd
dir token.pickle
```

---

## Estrutura de Diretórios

```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\
├── sync_incremental_completo.py         # Sync incremental completo
├── run_sync.py                           # Sync completo
├── scripts/
│   └── export/
│       ├── export_analise_posicoes.py    # Exporta vw_analise_posicoes
│       ├── export_funil_performance.py   # Exporta vw_funil_performance
│       └── export_dados_jade.py          # Exporta vw_dados_jade
├── services/
│   ├── sync_service.py                   # Lógica de sincronização
│   ├── api_client.py                     # Cliente da API
│   └── google_sheets_service.py          # Serviço Google Sheets
├── models/
│   └── database.py                       # Modelos SQLAlchemy
├── logs/
│   └── inhire_sync.log                   # Logs de sincronização
├── .env                                  # Variáveis de ambiente
├── credentials.json                      # Credenciais Google OAuth2
├── token.pickle                          # Token OAuth2 em cache
├── CLAUDE.md                             # Resumo executivo
├── COMANDOS_RAPIDOS.md                   # Este arquivo
└── docs/guides/                          # Documentação detalhada
```

---

## Informações Importantes

### Credenciais PostgreSQL
- **Host:** localhost
- **Porta:** 5432
- **Database:** inhire
- **User:** postgres
- **Password:** (ver `.env`)

### Credenciais API Inhire
- **Base URL:** https://api.inhire.app/
- **Auth URL:** https://auth.inhire.app/
- **Tenant:** frameworkdigital
- **Service Account:** service-account-ca4e275d-e401-4c08-8a52-28b251a05840@inhire.app

### Correção Crítica (2026-03-10)
✅ **Position Timeline** agora sincroniza corretamente no modo COMPLETO
- Arquivo modificado: `services/sync_service.py`
- Localização: Linha ~892
- Status: Testado e validado

---

## Suporte

- **Documentação completa:** `docs/guides/`
- **Resumo executivo:** `CLAUDE.md`
- **Logs:** `logs/inhire_sync.log`
- **Guia Google Sheets:** `docs/guides/GUIA_GOOGLE_SHEETS_INTEGRATION.md`

---

*Última atualização: 2026-03-10 - Versão 2.0*
