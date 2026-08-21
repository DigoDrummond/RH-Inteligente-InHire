# Rotinas de Sincronização e Exportação - Inhire

**Data:** 2026-08-20
**Versão:** 1.0
**Para:** Agendador de Tarefas do Windows

---

## 📋 Índice

1. [Rotinas de Sincronização](#rotinas-de-sincronização)
2. [Rotinas de Exportação](#rotinas-de-exportação)
3. [Rotinas de Backup](#rotinas-de-backup)
4. [Rotinas de Manutenção](#rotinas-de-manutenção)
5. [Ordem de Execução](#ordem-de-execução)
6. [Scripts .BAT Prontos](#scripts-bat-prontos)

---

## 1. ROTINAS DE SINCRONIZAÇÃO

### 1.1 Sync FULL (Completa)

**Quando executar:** 1x por semana (Domingo às 02:00)

**Duração:** ~55 minutos

**Comando Python:**
```bash
python run_sync.py --full
```

**Script BAT:** `rotinas/sync_full.bat`
```batch
@echo off
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
echo [%date% %time%] Iniciando Sync FULL >> logs\rotinas.log
python run_sync.py --full >> logs\sync_full.log 2>&1
echo [%date% %time%] Sync FULL concluido >> logs\rotinas.log
```

**O que faz:**
- Sincroniza 100% dos dados de todas as tabelas
- Busca todos os registros da API Inhire
- Usado na primeira vez ou para reconstruir base completa
- 11 entidades: Vagas, Posições, Position Timeline, Candidaturas, Talentos, Requisições, Scorecard Interviews, Scorecard Jobs, Vaga Tags, Clientes, Custom Fields

**Tabelas afetadas:**
- `vagas` (~2.000 registros)
- `posicoes` (~1.400 registros)
- `position_timeline` (~20.000 registros)
- `candidaturas` (~85.000 registros)
- `talentos` (~62.000 registros)
- `requisicoes` (~1.500 registros)
- `scorecard_interviews` (~5.000 registros)
- `scorecard_jobs` (~300 registros)
- `vaga_tags` (~800 registros)
- `clientes` (~200 registros)
- `custom_fields` (variável)

---

### 1.2 Sync INCREMENTAL (Atualização)

**Quando executar:** 2x por dia (08:00 e 20:00)

**Duração:** ~40-50 minutos

**Comando Python:**
```bash
python sync_incremental_completo.py --completa --yes
```

**Script BAT:** `rotinas/sync_incremental.bat`
```batch
@echo off
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
echo [%date% %time%] Iniciando Sync INCREMENTAL >> logs\rotinas.log
python sync_incremental_completo.py --completa --yes >> logs\sync_incremental.log 2>&1
echo [%date% %time%] Sync INCREMENTAL concluido >> logs\rotinas.log
```

**O que faz:**
- Sincroniza apenas registros modificados desde última execução
- 100% de cobertura (todas as entidades)
- Validações e alertas habilitados
- Skip rate médio: 90-95% (apenas ~10% dos dados mudam)

**Pré-requisito:**
- Deve ter executado Sync FULL pelo menos uma vez

**Taxa de atualização esperada:**
- Vagas: ~5-10% atualizadas
- Posições: ~10-15% atualizadas
- Candidaturas: ~15-20% atualizadas
- Talentos: ~1-2% atualizados

---

## 2. ROTINAS DE EXPORTAÇÃO

### 2.1 Export Views para Google Sheets (Principal)

**Quando executar:** Após sync incremental (08:30 e 20:30) ou manual

**Duração:** ~10-20 segundos

**Comando Python:**
```bash
python scripts/export/export_views_oauth.py
```

**Script BAT:** `rotinas/export_sheets.bat`
```batch
@echo off
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
echo [%date% %time%] Iniciando Export Google Sheets >> logs\rotinas.log
python scripts/export/export_views_oauth.py >> logs\export.log 2>&1
echo [%date% %time%] Export concluido >> logs\rotinas.log
```

**O que faz:**
- Exporta views SQL para Google Sheets
- Views exportadas (verificar no código quais):
  - `vw_analise_posicoes`
  - `vw_dados_jade`

**Planilha destino:** https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw

---

### 2.2 Export Análise de Posições

**Quando executar:** Manual ou agendado (diário 09:00)

**Duração:** ~15 segundos

**Comando Python:**
```bash
python scripts/export/export_analise_posicoes.py
```

**Script BAT:** `rotinas/export_analise_posicoes.bat`
```batch
@echo off
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
echo [%date% %time%] Iniciando Export Analise Posicoes >> logs\rotinas.log
python scripts/export/export_analise_posicoes.py >> logs\export_analise.log 2>&1
echo [%date% %time%] Export Analise concluido >> logs\rotinas.log
```

**O que faz:**
- Exporta view `vw_analise_posicoes` (1.383 registros × 34 colunas)

**Planilha destino:** https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw

**Aba:** `Teste_API`

---

### 2.3 Export Funil de Performance

**Quando executar:** Manual ou agendado (semanal - Segunda 09:00)

**Duração:** ~20 segundos

**Comando Python:**
```bash
python scripts/export/export_funil_performance.py
```

**Script BAT:** `rotinas/export_funil.bat`
```batch
@echo off
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
echo [%date% %time%] Iniciando Export Funil Performance >> logs\rotinas.log
python scripts/export/export_funil_performance.py >> logs\export_funil.log 2>&1
echo [%date% %time%] Export Funil concluido >> logs\rotinas.log
```

**O que faz:**
- Exporta view `vw_funil_performance` (~85.000 registros)

**Planilha destino:** https://docs.google.com/spreadsheets/d/1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0

---

### 2.4 Export Dados Jade

**Quando executar:** Manual ou agendado (diário 09:15)

**Duração:** ~10 segundos

**Comando Python:**
```bash
python scripts/export/export_dados_jade.py
```

**Script BAT:** `rotinas/export_dados_jade.bat`
```batch
@echo off
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
echo [%date% %time%] Iniciando Export Dados Jade >> logs\rotinas.log
python scripts/export/export_dados_jade.py >> logs\export_jade.log 2>&1
echo [%date% %time%] Export Dados Jade concluido >> logs\rotinas.log
```

**O que faz:**
- Exporta view `vw_dados_jade` (~689 registros)

**Planilha destino:** https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw

**Aba:** `API_Dados_Jade`

---

### 2.5 Export Relatório de Candidaturas

**Quando executar:** Manual ou agendado (diário 09:30)

**Duração:** ~15 segundos

**Comando Python:**
```bash
python scripts/export/export_relatorio_candidaturas.py
```

**Script BAT:** `rotinas/export_candidaturas.bat`
```batch
@echo off
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
echo [%date% %time%] Iniciando Export Relatorio Candidaturas >> logs\rotinas.log
python scripts/export/export_relatorio_candidaturas.py >> logs\export_candidaturas.log 2>&1
echo [%date% %time%] Export Candidaturas concluido >> logs\rotinas.log
```

**O que faz:**
- Exporta view `vw_relatorio_candidaturas` (~35.162 registros × 14 colunas)
- Inclui expansão automática da aba se necessário

**Planilha destino:** https://docs.google.com/spreadsheets/d/1E6Bv5JkL7Bmlj_v02FArthRlG07sBdwSOYAVbtTSKTQ

**Aba:** `[INHIRE]_relatorio_candidaturas`

---

## 3. ROTINAS DE BACKUP

### 3.1 Backup Completo do Banco de Dados

**Quando executar:** Diário às 01:00 (ANTES de qualquer sync)

**Duração:** ~5-10 minutos

**Comando:**
```batch
scripts\backup\backup_inhire_windows.bat
```

**Script BAT:** `rotinas/backup_bd.bat`
```batch
@echo off
echo [%date% %time%] Iniciando Backup BD >> logs\rotinas.log
call "scripts\backup\backup_inhire_windows.bat" >> logs\backup.log 2>&1
echo [%date% %time%] Backup BD concluido >> logs\rotinas.log
```

**O que faz:**
- Backup completo do PostgreSQL (banco inhire)
- Formato custom compactado (.dump)
- Armazena em `Backup_BD_Inhire/full/`
- Nomenclatura: `inhire_backup_YYYYMMDD_HHMMSS.dump`

**Pré-requisito:**
- Variável de ambiente `PGPASSWORD` configurada
- PostgreSQL 18 instalado

---

## 4. ROTINAS DE MANUTENÇÃO

### 4.1 Health Check

**Quando executar:** Diário às 06:00

**Duração:** <1 minuto

**Comando Python:**
```bash
python health_check.py
```

**Script BAT:** `rotinas/health_check.bat`
```batch
@echo off
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
echo [%date% %time%] Iniciando Health Check >> logs\rotinas.log
python health_check.py >> logs\health_check.log 2>&1
echo [%date% %time%] Health Check concluido >> logs\rotinas.log
```

**O que faz:**
- Verifica conectividade com API Inhire
- Verifica conectividade com PostgreSQL
- Verifica espaço em disco
- Verifica logs de erro
- Gera relatório de saúde

---

## 5. ORDEM DE EXECUÇÃO

### 5.1 Rotina Diária (Segunda a Sábado)

```
HORA  | ROTINA                    | DURAÇÃO | TIPO
------|---------------------------|---------|-------------
01:00 | Backup BD                 | 10 min  | Manutenção
06:00 | Health Check              | 1 min   | Manutenção
08:00 | Sync INCREMENTAL          | 45 min  | Sincronização
08:30 | Export Sheets (Principal) | 20 seg  | Exportação
09:00 | Export Análise Posições   | 15 seg  | Exportação
09:15 | Export Dados Jade         | 10 seg  | Exportação
09:30 | Export Candidaturas       | 15 seg  | Exportação
20:00 | Sync INCREMENTAL          | 45 min  | Sincronização
20:30 | Export Sheets (Principal) | 20 seg  | Exportação
```

### 5.2 Rotina Semanal (Domingo)

```
HORA  | ROTINA                    | DURAÇÃO | TIPO
------|---------------------------|---------|-------------
01:00 | Backup BD                 | 10 min  | Manutenção
02:00 | Sync FULL (Completa)      | 55 min  | Sincronização
03:00 | Export Sheets (Principal) | 20 seg  | Exportação
06:00 | Health Check              | 1 min   | Manutenção
```

### 5.3 Rotina Segunda-feira (Adicional)

```
HORA  | ROTINA                    | DURAÇÃO | TIPO
------|---------------------------|---------|-------------
09:00 | Export Funil Performance  | 20 seg  | Exportação (semanal)
```

---

## 6. SCRIPTS .BAT PRONTOS

### 6.1 Estrutura de Diretórios

```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\
├── rotinas/
│   ├── sync_full.bat
│   ├── sync_incremental.bat
│   ├── backup_bd.bat
│   ├── health_check.bat
│   ├── export_sheets.bat
│   ├── export_analise_posicoes.bat
│   ├── export_funil.bat
│   ├── export_dados_jade.bat
│   └── export_candidaturas.bat
└── logs/
    ├── rotinas.log (log consolidado)
    ├── sync_full.log
    ├── sync_incremental.log
    ├── backup.log
    ├── health_check.log
    ├── export.log
    ├── export_analise.log
    ├── export_funil.log
    ├── export_jade.log
    └── export_candidaturas.log
```

### 6.2 Script Master de Rotina Diária

**Arquivo:** `rotinas/rotina_diaria.bat`

```batch
@echo off
REM ============================================================================
REM ROTINA DIARIA - Sync Incremental + Exports
REM ============================================================================
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo ROTINA DIARIA INHIRE - %date% %time%
echo ============================================================================
echo.

REM 1. Sync Incremental
echo [1/5] Executando Sync INCREMENTAL...
call rotinas\sync_incremental.bat
if errorlevel 1 (
    echo ERRO: Sync INCREMENTAL falhou!
    exit /b 1
)
echo.

REM 2. Export Sheets Principal
echo [2/5] Exportando para Google Sheets...
call rotinas\export_sheets.bat
echo.

REM 3. Export Análise Posições
echo [3/5] Exportando Analise Posicoes...
call rotinas\export_analise_posicoes.bat
echo.

REM 4. Export Dados Jade
echo [4/5] Exportando Dados Jade...
call rotinas\export_dados_jade.bat
echo.

REM 5. Export Candidaturas
echo [5/5] Exportando Candidaturas...
call rotinas\export_candidaturas.bat
echo.

echo ============================================================================
echo ROTINA DIARIA CONCLUIDA - %date% %time%
echo ============================================================================
```

### 6.3 Script Master de Rotina Semanal (Domingo)

**Arquivo:** `rotinas/rotina_semanal.bat`

```batch
@echo off
REM ============================================================================
REM ROTINA SEMANAL (DOMINGO) - Sync FULL + Backup
REM ============================================================================
cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo ROTINA SEMANAL INHIRE - %date% %time%
echo ============================================================================
echo.

REM 1. Backup
echo [1/3] Executando Backup BD...
call rotinas\backup_bd.bat
if errorlevel 1 (
    echo ERRO: Backup falhou!
    exit /b 1
)
echo.

REM 2. Sync FULL
echo [2/3] Executando Sync FULL (pode levar 55 min)...
call rotinas\sync_full.bat
if errorlevel 1 (
    echo ERRO: Sync FULL falhou!
    exit /b 1
)
echo.

REM 3. Export Sheets
echo [3/3] Exportando para Google Sheets...
call rotinas\export_sheets.bat
echo.

echo ============================================================================
echo ROTINA SEMANAL CONCLUIDA - %date% %time%
echo ============================================================================
```

---

## 7. CONFIGURAÇÃO NO AGENDADOR DE TAREFAS DO WINDOWS

### 7.1 Tarefa 1: Backup Diário

- **Nome:** Inhire - Backup BD Diário
- **Descrição:** Backup diário do banco PostgreSQL
- **Ação:** `C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\backup_bd.bat`
- **Gatilho:** Diário às 01:00
- **Executar com:** Privilégios mais altos
- **Executar mesmo se:** Usuário não estiver logado

### 7.2 Tarefa 2: Health Check

- **Nome:** Inhire - Health Check Diário
- **Ação:** `C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\health_check.bat`
- **Gatilho:** Diário às 06:00

### 7.3 Tarefa 3: Sync Incremental + Exports (Manhã)

- **Nome:** Inhire - Sync Incremental Manhã
- **Ação:** `C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\rotina_diaria.bat`
- **Gatilho:** Segunda a Sábado às 08:00

### 7.4 Tarefa 4: Sync Incremental + Exports (Noite)

- **Nome:** Inhire - Sync Incremental Noite
- **Ação:** `C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\sync_incremental.bat`
- **Gatilho:** Segunda a Sábado às 20:00
- **Seguido por:** `export_sheets.bat` (usar "Iniciar outra tarefa" após conclusão)

### 7.5 Tarefa 5: Sync FULL Semanal (Domingo)

- **Nome:** Inhire - Sync FULL Semanal
- **Ação:** `C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\rotina_semanal.bat`
- **Gatilho:** Domingo às 02:00
- **Tempo máximo:** 2 horas

### 7.6 Tarefa 6: Export Funil Performance Semanal

- **Nome:** Inhire - Export Funil Semanal
- **Ação:** `C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\export_funil.bat`
- **Gatilho:** Segunda-feira às 09:00

---

## 8. MONITORAMENTO E ALERTAS

### 8.1 Verificar Logs

**Log consolidado:**
```
logs\rotinas.log
```

**Logs individuais:**
```
logs\sync_full.log
logs\sync_incremental.log
logs\backup.log
logs\export.log
```

### 8.2 Verificar Última Sincronização

**Query SQL:**
```sql
SELECT
    sync_type,
    sync_entity,
    status,
    start_time AT TIME ZONE 'America/Sao_Paulo' as inicio,
    end_time AT TIME ZONE 'America/Sao_Paulo' as fim,
    EXTRACT(EPOCH FROM (end_time - start_time))/60 as duracao_minutos,
    records_processed,
    records_created,
    records_updated
FROM sync_log
WHERE sync_type IN ('FULL', 'INCREMENTAL')
ORDER BY start_time DESC
LIMIT 10;
```

### 8.3 Alertas Recomendados

**Configurar alertas para:**
1. Sync falhou (erro no log)
2. Backup falhou
3. Export falhou
4. Duração > 2x esperada (possível problema)
5. Taxa de falhas > 1%

---

## 9. TROUBLESHOOTING

### 9.1 Problema: Sync INCREMENTAL demora >60 min

**Causa:** Muitos dados modificados ou performance degradada

**Solução:**
1. Verificar skip rate no log (deve ser >70%)
2. Executar Sync FULL se skip rate < 50%
3. Verificar índices do banco: `scripts/debug/check_database_indexes.py`

### 9.2 Problema: Export falha com "grid limits"

**Causa:** Google Sheets tem limite de linhas

**Solução:**
- Script `export_relatorio_candidaturas.py` tem expansão automática
- Outros scripts: expandir aba manualmente ou usar script corrigido

### 9.3 Problema: Backup falha

**Causa:** Senha PostgreSQL incorreta ou espaço em disco

**Solução:**
1. Verificar variável `PGPASSWORD`
2. Verificar espaço em disco: `Backup_BD_Inhire/`
3. Deletar backups antigos (>30 dias)

---

## 10. RESUMO EXECUTIVO

### Rotinas CRÍTICAS (Obrigatórias)

| Rotina | Frequência | Duração | Prioridade |
|--------|------------|---------|------------|
| Backup BD | Diário 01:00 | 10 min | 🔴 CRÍTICA |
| Sync FULL | Domingo 02:00 | 55 min | 🔴 CRÍTICA |
| Sync INCREMENTAL | 2x/dia (08:00, 20:00) | 45 min | 🔴 CRÍTICA |

### Rotinas IMPORTANTES (Recomendadas)

| Rotina | Frequência | Duração | Prioridade |
|--------|------------|---------|------------|
| Export Sheets | Após sync | 20 seg | 🟡 ALTA |
| Health Check | Diário 06:00 | 1 min | 🟡 ALTA |
| Export Candidaturas | Diário 09:30 | 15 seg | 🟡 ALTA |

### Rotinas OPCIONAIS (Sob Demanda)

| Rotina | Frequência | Duração | Prioridade |
|--------|------------|---------|------------|
| Export Funil | Semanal | 20 seg | 🟢 MÉDIA |
| Export Análise | Diário | 15 seg | 🟢 MÉDIA |
| Export Jade | Diário | 10 seg | 🟢 MÉDIA |

---

**Fim do Documento**
