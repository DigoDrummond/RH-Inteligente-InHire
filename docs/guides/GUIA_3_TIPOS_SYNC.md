# 🔄 Guia: 3 Tipos de Sincronização

## Visão Geral

O projeto possui **3 tipos** de sincronização, cada uma otimizada para um cenário específico:

| Tipo | Arquivo | Tempo | Frequência | Uso |
|------|---------|-------|------------|-----|
| **Completa** | `sync_completa.py` | ~55 min | 1x semana | Carga inicial, validação |
| **Incremental Completa** | `sync_incremental_completa.py` | ~10-20 min | 2-4 horas | Manutenção geral |
| **Incremental Rápida** | `sync_incremental_rapida.py` | < 3 min | 30 min | Tempo real |

---

## 1. Sincronização Completa

### 📋 Características

```bash
python sync_completa.py
```

**O que faz:**
- ✅ Busca **TODAS** as entidades da API
- ✅ Atualiza **TODOS** os registros (sem skip)
- ✅ 100% de cobertura garantida
- ⏱️ Tempo: ~55 minutos

**Dados processados:**
- Vagas: 1.088 (todas)
- Posições: ~540 (todas)
- Candidaturas: ~75.000 (todas)
- Talentos: ~53.000 (todos)

**Quando usar:**
- ✅ Primeira vez (carga inicial)
- ✅ 1x por semana (domingo 02:00)
- ✅ Após mudanças estruturais no banco
- ✅ Validação periódica de integridade

**Quando NÃO usar:**
- ❌ Para sincronização frequente (desperdício de recursos)
- ❌ Para monitoramento em tempo real (muito lenta)

---

## 2. Sincronização Incremental Completa

### 📋 Características

```bash
python sync_incremental_completa.py
```

**O que faz:**
- ✅ Busca **TODAS** as entidades da API
- ✅ Compara datas (`data_API > data_BD`)
- ✅ **SKIP** registros não modificados (98% skip rate!)
- ⏱️ Tempo: ~10-20 minutos

**Lógica de comparação:**
```python
if data_API > data_BD:
    → UPDATE (registro modificado)
else:
    → SKIP (registro já atualizado)
```

**Resultados típicos:**
```
Vagas:
  Processados:  1.088
  Criados:      0
  Atualizados:  17
  Ignorados:    1.071  ← 98.4% skip!
  Falhas:       0

Posições:
  Processados:  542
  Criados:      0
  Atualizados:  3
  Ignorados:    539

Candidaturas:
  Processados:  75.282
  Criados:      120
  Atualizados:  45
  Ignorados:    75.117  ← 99.8% skip!
  Falhas:       0

Talentos:
  Processados:  53.068
  Criados:      5
  Atualizados:  8
  Ignorados:    53.055
```

**Quando usar:**
- ✅ Manutenção geral (2-4 horas)
- ✅ Capturar mudanças em vagas fechadas/canceladas
- ✅ Garantir 100% dos dados atualizados
- ✅ Validação diária

**Quando NÃO usar:**
- ❌ Para sincronização a cada 30 min (muito lenta)
- ❌ Primeira carga (use sync_completa.py)

---

## 3. Sincronização Incremental Rápida ⚡

### 📋 Características

```bash
python sync_incremental_rapida.py
```

**O que faz:**
- ✅ Busca APENAS vagas **modificadas recentemente** (últimas 2 horas)
- ✅ Processa APENAS posições/candidaturas das vagas filtradas
- ✅ **Smart Talent Sync**: busca APENAS talentos NOVOS (não existentes no BD)
- ✅ Compara datas (`data_API > data_BD`)
- ⏱️ **Tempo: < 3 minutos** (META!)

**⚠️ IMPORTANTE - Status Reais da API InHire:**
- ✅ OPEN (29 vagas / 3%)
- ✅ CLOSED (784 vagas / 72%)
- ✅ CANCELED (275 vagas / 25%)
- ❌ **PAUSED NÃO EXISTE**

**Filtros aplicados:**

1. **Vagas:**
   ```python
   # ✅ OTIMIZADO: Filtro por data de atualização
   from datetime import datetime, timedelta
   import pytz

   sp_tz = pytz.timezone('America/Sao_Paulo')
   cutoff_time = datetime.now(sp_tz) - timedelta(hours=2)

   for vaga in all_vagas_api:
       if vaga.updatedAt >= cutoff_time:
           → PROCESSAR  # Qualquer vaga modificada nas últimas 2h
   ```

   **Justificativa:**
   - Filtro por status (OPEN/PAUSED) retorna 0 vagas
   - PAUSED não existe na API InHire
   - Vagas podem mudar de OPEN → CLOSED → CANCELED
   - Data de atualização captura TODAS as mudanças

2. **Talentos:**
   ```python
   # Coletar IDs das candidaturas
   talent_ids = {cand.talentId for cand in candidaturas}

   # Verificar quais JÁ EXISTEM no BD
   existing_ids = session.query(Talento.inhire_id).filter(
       Talento.inhire_id.in_(talent_ids)
   ).all()

   # Buscar APENAS os NOVOS
   new_ids = talent_ids - existing_ids

   → Buscar apenas new_ids da API (economiza 99% das requisições!)
   ```

**Resultados esperados:**
```
Vagas filtradas:   ~15/1.088 (1.4%)  ← Apenas ativas/recentes
Posições:          ~20  ← Das vagas filtradas
Candidaturas:      ~150  ← Das vagas filtradas
Talentos novos:    ~5  ← Apenas IDs novos

Tempo:             ~2 minutos ✅
META:              < 3 minutos ✅
```

**Quando usar:**
- ✅ **Sincronização a cada 30 minutos** (tempo real)
- ✅ Monitoramento de vagas ativas
- ✅ Capturar mudanças recentes
- ✅ Produção com alta frequência

**Quando NÃO usar:**
- ❌ Primeira carga (use sync_completa.py)
- ❌ Para capturar mudanças em vagas fechadas (use sync_incremental_completa.py)

---

## Comparação Lado a Lado

### Performance

| Métrica | Completa | Inc. Completa | Inc. Rápida |
|---------|----------|---------------|-------------|
| **Tempo** | ~55 min | ~10-20 min | **< 3 min** |
| **Vagas processadas** | 1.088 | 1.088 | ~15 |
| **Posições processadas** | ~540 | ~540 | ~20 |
| **Candidaturas processadas** | ~75k | ~75k | ~150 |
| **Talentos buscados API** | ~53k | ~53k | **~5** |
| **Writes no BD** | 100% | ~2% | ~0.5% |
| **Eficiência** | Baixa | Alta | **Muito Alta** |

### Cobertura

| Aspecto | Completa | Inc. Completa | Inc. Rápida |
|---------|----------|---------------|-------------|
| **Vagas fechadas** | ✅ Sim | ✅ Sim | ❌ Não |
| **Vagas canceladas** | ✅ Sim | ✅ Sim | ❌ Não |
| **Vagas antigas** | ✅ Sim | ✅ Sim | ❌ Não |
| **Vagas ativas** | ✅ Sim | ✅ Sim | ✅ Sim |
| **Mudanças recentes** | ✅ Sim | ✅ Sim | ✅ Sim |
| **100% dos dados** | ✅ Sim | ✅ Sim | ❌ Não |

### Comparação de Datas

| Tipo | Compara Datas? | Skip Logic |
|------|----------------|------------|
| **Completa** | ❌ Não | Sempre atualiza |
| **Inc. Completa** | ✅ Sim | `data_API > data_BD` |
| **Inc. Rápida** | ✅ Sim | `data_API > data_BD` + filtros |

---

## Estratégia Recomendada

### Agendamento Ideal

```python
# scheduler.py

from apscheduler.schedulers.blocking import BlockingScheduler
from sync_completa import sync_completa
from sync_incremental_completa import sync_incremental_completa
from sync_incremental_rapida import sync_incremental_rapida

scheduler = BlockingScheduler()

# 1. Incremental RÁPIDA: a cada 30 minutos (horário comercial)
scheduler.add_job(
    sync_incremental_rapida,
    'cron',
    minute='*/30',  # :00, :30
    hour='7-19',    # 07:00 - 19:00
    id='sync_rapida_30min'
)

# 2. Incremental COMPLETA: a cada 4 horas (noturno também)
scheduler.add_job(
    sync_incremental_completa,
    'cron',
    hour='*/4',  # 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
    id='sync_incremental_4h'
)

# 3. Completa: domingo 02:00
scheduler.add_job(
    sync_completa,
    'cron',
    day_of_week='sun',
    hour=2,
    minute=0,
    id='sync_completa_semanal'
)

scheduler.start()
```

### Frequências

| Sync | Frequência | Horário | Motivo |
|------|-----------|---------|--------|
| **Rápida** | 30 min | 07:00-19:00 | Captura mudanças em tempo real |
| **Completa Inc.** | 4 horas | 24/7 | Garante completude |
| **Completa** | Semanal | Dom 02:00 | Validação total |

---

## Como Escolher?

### Use `sync_completa.py` se:
- ✅ É a primeira vez que sincroniza
- ✅ Quer 100% de garantia dos dados
- ✅ Suspeita de inconsistências
- ✅ Mudou estrutura do banco

### Use `sync_incremental_completa.py` se:
- ✅ Quer atualizar tudo, mas de forma eficiente
- ✅ Precisa capturar mudanças em vagas fechadas/canceladas
- ✅ Executa a cada 2-4 horas
- ✅ Quer 100% de cobertura com 98% de skip

### Use `sync_incremental_rapida.py` se:
- ✅ **Quer sincronização a cada 30 minutos**
- ✅ Foca APENAS em vagas ativas
- ✅ Precisa de resposta rápida (< 3 min)
- ✅ Quer monitoramento em tempo real

---

## Monitoramento

### Ver última sincronização

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "
SELECT
    sync_type,
    sync_entity,
    status,
    start_time AT TIME ZONE 'America/Sao_Paulo' as inicio,
    end_time AT TIME ZONE 'America/Sao_Paulo' as fim,
    records_processed,
    records_created,
    records_updated
FROM sync_log
ORDER BY start_time DESC
LIMIT 10;
"
```

### Verificar contagem atual

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "
SELECT
    (SELECT COUNT(*) FROM vagas) as vagas,
    (SELECT COUNT(*) FROM posicoes) as posicoes,
    (SELECT COUNT(*) FROM candidaturas) as candidaturas,
    (SELECT COUNT(*) FROM talentos) as talentos;
"
```

---

## Conclusão

**3 tipos de sincronização, 3 cenários diferentes:**

1. **Completa** → Primeira carga, validação semanal
2. **Incremental Completa** → Manutenção geral, 100% de cobertura
3. **Incremental Rápida** → **Tempo real (30 min), foco em vagas ativas** ⚡

**Escolha a ferramenta certa para o trabalho certo!** 🎯
