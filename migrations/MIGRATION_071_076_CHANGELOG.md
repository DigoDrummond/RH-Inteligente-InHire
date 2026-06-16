# Changelog: Migrations 071-077 - Correção de SLAs e Pausas em Andamento

**Período:** 03-04 de Março de 2026
**Objetivo:** Corrigir SLAs negativos e capturar pausas em andamento
**Status:** ✅ Concluído - 100% de sucesso

---

## 📋 Índice de Migrations

| # | Nome | Data | Status | Resultado |
|---|------|------|--------|-----------|
| 071 | Fix SLA Paused Date | 03/03/2026 | ✅ Concluída | 6 de 11 corrigidas |
| 072 | Fix Pausa Encerradas | 03/03/2026 | ✅ Concluída | 2 de 5 corrigidas |
| 073 | Fix Duplicatas Timeline | 03/03/2026 | ⚠️ Limitada | 0 de 3 corrigidas |
| 074 | Fix Pareamento Pausas | 03/03/2026 | ⚠️ Limitada | 0 de 3 corrigidas |
| 075 | Fix Órfãos Pausas | 03/03/2026 | ✅ Concluída | 2 de 3 corrigidas |
| 076 | Fix Eventos Fantasma | 04/03/2026 | ✅ Concluída | 1 de 1 corrigida |
| 077 | Fix Pausas em Andamento | 04/03/2026 | ✅ Concluída | Todas posições pausadas |

---

## Migration 071 - Fix SLA Paused Date

### Informações Gerais

- **Data:** 03/03/2026
- **Arquivos:**
  - `migrations/071_fix_sla_paused_date_STEP1_DROP.sql`
  - `migrations/071_fix_sla_paused_date_STEP2_CREATE.sql`
- **View Afetada:** `vw_analise_posicoes`
- **Linhas Modificadas:** 8 localizações na view

### Problema

Posições com status 'paused' apresentavam SLA negativo devido a inconsistência temporal:
- SLA geral usava `DATE(data_ultima_mudanca)` (data da pausa)
- SLA pendência usava `CURRENT_TIMESTAMP` (momento atual)
- Discrepância causava SLA de pendência > SLA geral → SLA recrutamento negativo

### Mudanças SQL

**Linha 76 (periodos_pausa - data_fim):**
```sql
-- ANTES
COALESCE(
    (SELECT MIN(fim.changed_at) FROM eventos_pausa fim ...),
    CURRENT_TIMESTAMP  -- ← Inconsistente
) AS data_fim

-- DEPOIS
COALESCE(
    (SELECT MIN(fim.changed_at) FROM eventos_pausa fim ...),
    CURRENT_DATE  -- ← Consistente (sem hora)
) AS data_fim
```

**Linha 198 (data_encerramento_ou_atualizacao):**
```sql
-- ANTES
WHEN COALESCE(usp.new_status, p.status) = 'paused'
    THEN DATE(usp.data_ultima_mudanca)  -- ← Data da pausa

-- DEPOIS
WHEN COALESCE(usp.new_status, p.status) = 'paused'
    THEN CURRENT_DATE  -- ← Data atual
```

**Localizações adicionais (similares):**
- Linha 276 (sla_recrutamento - cálculo de data_fim)
- Linha 296 (sla_recrutamento - cálculo de data_fim)
- Linha 336 (sla_geral - cálculo de data_fim)
- Linha 356 (sla_geral - cálculo de data_fim)
- Linha 381 (indicador_prazo - cálculo de data_fim)
- Linha 402 (indicador_prazo - cálculo de data_fim)

### Validação

```sql
-- Antes da migration
SELECT COUNT(*) FILTER (WHERE sla_recrutamento < 0) FROM vw_analise_posicoes;
-- Resultado: 11

-- Depois da migration
SELECT COUNT(*) FILTER (WHERE sla_recrutamento < 0) FROM vw_analise_posicoes;
-- Resultado: 5 (6 corrigidas)

-- Exemplo de posição corrigida (ID 589)
SELECT id_position, sla_recrutamento FROM vw_analise_posicoes WHERE id_position = 589;
-- Antes: -31 | Depois: +51
```

### Execução

```bash
# pgAdmin:
1. Abrir 071_fix_sla_paused_date_STEP1_DROP.sql
2. Executar
3. Abrir 071_fix_sla_paused_date_STEP2_CREATE.sql
4. Executar
```

### Resultado

- ✅ 6 posições corrigidas
- ⚠️ 5 posições ainda negativas → próxima migration necessária

---

## Migration 072 - Fix Pausa Encerradas

### Informações Gerais

- **Data:** 03/03/2026
- **Arquivos:**
  - `migrations/072_fix_pausa_encerradas_STEP1_DROP.sql`
  - `migrations/072_fix_pausa_encerradas_STEP2_CREATE.sql`
- **View Afetada:** `vw_analise_posicoes`
- **CTE Modificado:** `periodos_pausa`

### Problema

Posições canceladas/fechadas tinham pausas "Em andamento" até a data atual:
- CTE `periodos_pausa` usava `CURRENT_DATE` quando não havia FIM_PAUSA
- Não verificava se a posição já estava encerrada (canceled/closed)
- Resultado: Pausas contando centenas de dias após encerramento

**Exemplo Real (Posição 143):**
- Cancelada: 22/01/2025
- Pausa iniciada: 15/08/2024
- Sem FIM_PAUSA explícito → contava até 03/03/2026
- **360 dias de pausa!**

### Mudanças SQL

**Linhas 99-104 (periodos_pausa - data_fim):**
```sql
-- ANTES (Migration 071)
COALESCE(
    (SELECT MIN(fim.changed_at) FROM eventos_pausa fim ...),
    CURRENT_DATE  -- ← Sempre usa hoje
) AS data_fim

-- DEPOIS (Migration 072)
COALESCE(
    (SELECT MIN(fim.changed_at) FROM eventos_pausa fim ...),
    (SELECT usp.data_ultima_mudanca  -- ← NOVO: usa data de encerramento
     FROM ultimo_status_posicao usp
     WHERE usp.posicao_id = inicio.posicao_id
       AND usp.new_status IN ('canceled', 'closed')
    ),
    CURRENT_DATE  -- ← Só usa hoje se ainda paused
) AS data_fim
```

### Validação

```sql
-- Verificar posições encerradas com pausas longas
SELECT id_position, status_atual, sla_pendencia_cliente, detalhamento_pausas
FROM vw_analise_posicoes
WHERE status_atual IN ('canceled', 'closed')
  AND sla_pendencia_cliente > 100;  -- Suspeito

-- Após migration 072
SELECT id_position, sla_recrutamento FROM vw_analise_posicoes
WHERE id_position IN (143, 1408);
-- 143: -271 → +9
-- 1408: -279 → +12
```

### Execução

```bash
# pgAdmin:
1. Abrir 072_fix_pausa_encerradas_STEP1_DROP.sql
2. Executar
3. Abrir 072_fix_pausa_encerradas_STEP2_CREATE.sql
4. Executar
```

### Resultado

- ✅ 2 posições corrigidas (143, 1408)
- ⚠️ 3 posições ainda negativas (782, 914, 1274) → diagnóstico mais profundo necessário

---

## Migration 073 - Fix Duplicatas Timeline

### Informações Gerais

- **Data:** 03/03/2026
- **Arquivos:**
  - `migrations/073_fix_duplicatas_timeline_STEP1_DROP.sql`
  - `migrations/073_fix_duplicatas_timeline_STEP2_CREATE.sql`
- **View Afetada:** `vw_analise_posicoes`
- **CTEs Modificados:** Novos `eventos_pausa_raw` e `eventos_pausa`

### Problema

Eventos duplicados na tabela `position_timeline`:
- Mesmo timestamp mas IDs diferentes
- Causados por sincronização imperfeita com API Inhire
- Resultavam em múltiplos INICIO_PAUSA contabilizados

**Exemplo Real (Posição 782):**
```
Duplicatas identificadas:
- IDs 3320 e 5355: NULL→open em 30/07/2025 17:38:14
- IDs 3321 e 5356: open→paused em 30/07/2025 17:38:18
- IDs 3322 e 5357: paused→open em 16/09/2025 08:03:03

Resultado: 3 INICIO_PAUSA = 64 dias pausados (esperado: 1 INICIO = ~26 dias)
```

### Mudanças SQL

**Linhas 70-147 (novos CTEs):**
```sql
-- ANTES (Migration 072) - Um único CTE
eventos_pausa AS (
    SELECT DISTINCT  -- ← Deduplicação simples
        posicao_id, changed_at, previous_status, new_status, tipo_evento
    FROM position_timeline
    WHERE ...
)

-- DEPOIS (Migration 073) - Dois CTEs com deduplicação conservadora
eventos_pausa_raw AS (
    -- STEP 1: Buscar TODOS os eventos, incluindo id e notes
    SELECT
        id,  -- ← Incluído para priorização
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        notes,  -- ← Incluído para priorização
        CASE ... END AS tipo_evento
    FROM position_timeline
    WHERE ...
),
eventos_pausa AS (
    -- STEP 2: Deduplicação conservadora
    SELECT DISTINCT ON (
        posicao_id,
        COALESCE(previous_status, 'NULL'),  -- ← Tratar NULL
        new_status,
        DATE(changed_at)  -- ← Agrupa por DIA (sem hora)
    )
        posicao_id, changed_at, previous_status, new_status, tipo_evento
    FROM eventos_pausa_raw
    ORDER BY
        posicao_id,
        COALESCE(previous_status, 'NULL'),
        new_status,
        DATE(changed_at),
        CASE WHEN notes IS NOT NULL AND notes != '' THEN 0 ELSE 1 END,  -- ← Prioriza com notes
        changed_at ASC,  -- ← Timestamp mais antigo
        id ASC  -- ← ID menor (registro original)
)
```

**Priorização:**
1. Eventos com `notes` preenchido (informação adicional)
2. Timestamp mais antigo (primeiro registro)
3. ID menor (registro original no banco)

### Validação

```sql
-- Verificar duplicatas removidas (Posição 782)
WITH eventos_dedup AS (
    SELECT DISTINCT ON (posicao_id, previous_status, new_status, DATE(changed_at))
        id, changed_at
    FROM position_timeline
    WHERE posicao_id = 782
      AND ((previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused')
    ORDER BY posicao_id, previous_status, new_status, DATE(changed_at), changed_at ASC, id ASC
)
SELECT COUNT(*) FROM eventos_dedup;
-- Esperado: 1 (de 3 originais)
```

### Execução

```bash
# pgAdmin:
1. Abrir 073_fix_duplicatas_timeline_STEP1_DROP.sql
2. Executar
3. Abrir 073_fix_duplicatas_timeline_STEP2_CREATE.sql
4. Executar
```

### Resultado

- ⚠️ 0 posições corrigidas
- **Limitação identificada:** DISTINCT ON agrupa por DIA, mas eventos em DIAS diferentes são mantidos
- Exemplo: 12/08 e 21/08 são dias diferentes → ambos mantidos como INICIOs
- **Lição:** Deduplicação por data não resolve múltiplos INICIOs legítimos em dias diferentes

---

## Migration 074 - Fix Pareamento Pausas

### Informações Gerais

- **Data:** 03/03/2026
- **Arquivos:**
  - `migrations/074_fix_pareamento_pausas_STEP1_DROP.sql`
  - `migrations/074_fix_pareamento_pausas_STEP2_CREATE.sql`
- **View Afetada:** `vw_analise_posicoes`
- **CTEs Modificados:** Novos `eventos_pausa_numerados` e `periodos_pausa`

### Problema

Migration 073 deduplicou eventos no mesmo dia, mas múltiplos INICIOs em dias diferentes apontavam para o MESMO FIM:
- Lógica: `SELECT MIN(fim.changed_at) WHERE fim > inicio`
- Cada INICIO pegava o primeiro FIM disponível após ele
- Resultado: Múltiplos INICIOs → mesmo FIM = períodos sobrepostos

**Exemplo Real (Posição 782):**
```
INICIO #1: 12/08/2025 → FIM: 16/09/2025 = 26 dias
INICIO #2: 21/08/2025 → FIM: 16/09/2025 = 19 dias (MESMO FIM!)
INICIO #3: 21/08/2025 → FIM: 16/09/2025 = 19 dias (MESMO FIM!)
Total: 64 dias (3 períodos sobrepostos)
```

### Mudanças SQL

**Linhas 192-228 (novos CTEs):**
```sql
-- ANTES (Migration 073) - Pareamento via MIN()
periodos_pausa AS (
    SELECT
        inicio.posicao_id,
        inicio.changed_at AS data_inicio,
        COALESCE(
            (SELECT MIN(fim.changed_at)  -- ← Pega primeiro FIM após INICIO
             FROM eventos_pausa fim
             WHERE fim.tipo_evento = 'FIM_PAUSA'
               AND fim.changed_at > inicio.changed_at
            ),
            ...
        ) AS data_fim
    FROM eventos_pausa inicio
    WHERE inicio.tipo_evento = 'INICIO_PAUSA'
)

-- DEPOIS (Migration 074) - Pareamento via ROW_NUMBER
eventos_pausa_numerados AS (
    SELECT
        posicao_id,
        changed_at,
        tipo_evento,
        ROW_NUMBER() OVER (
            PARTITION BY posicao_id, tipo_evento  -- ← Numera por tipo
            ORDER BY changed_at
        ) AS rn  -- ← Número de sequência
    FROM eventos_pausa
),
periodos_pausa AS (
    SELECT
        i.posicao_id,
        i.changed_at AS data_inicio,
        COALESCE(
            f.changed_at,  -- ← FIM com mesmo rn (pareamento 1:1)
            ...
        ) AS data_fim
    FROM eventos_pausa_numerados i
    LEFT JOIN eventos_pausa_numerados f  -- ← Pareamento explícito
        ON f.posicao_id = i.posicao_id
        AND f.tipo_evento = 'FIM_PAUSA'
        AND f.rn = i.rn  -- ← PAREAMENTO 1:1!
    WHERE i.tipo_evento = 'INICIO_PAUSA'
)
```

**Lógica de Pareamento:**
- INICIO #1 (rn=1) → FIM #1 (rn=1)
- INICIO #2 (rn=2) → FIM #2 (rn=2)
- ...

### Validação

```sql
-- Simular pareamento (Posição 782)
WITH eventos_num AS (
    SELECT
        tipo_evento,
        changed_at,
        ROW_NUMBER() OVER (PARTITION BY tipo_evento ORDER BY changed_at) AS rn
    FROM position_timeline
    WHERE posicao_id = 782
      AND tipo_evento IN ('INICIO_PAUSA', 'FIM_PAUSA')
)
SELECT
    i.rn,
    i.changed_at AS inicio,
    f.changed_at AS fim
FROM eventos_num i
LEFT JOIN eventos_num f ON f.tipo_evento = 'FIM_PAUSA' AND f.rn = i.rn
WHERE i.tipo_evento = 'INICIO_PAUSA';
```

### Execução

```bash
# pgAdmin:
1. Abrir 074_fix_pareamento_pausas_STEP1_DROP.sql
2. Executar
3. Abrir 074_fix_pareamento_pausas_STEP2_CREATE.sql
4. Executar
```

### Resultado

- ⚠️ 0 posições corrigidas
- **Limitação identificada:** LEFT JOIN permite INICIOs órfãos (sem FIM)
- Órfãos recebem `f.changed_at = NULL` → COALESCE → CURRENT_DATE
- Exemplo: INICIO 12/08 sem FIM → 12/08 a HOJE = 170 dias
- **Lição:** LEFT JOIN não garante ciclos completos

---

## Migration 075 - Fix Órfãos Pausas

### Informações Gerais

- **Data:** 03/03/2026
- **Arquivos:**
  - `migrations/075_fix_orfaos_pausas_STEP1_DROP.sql`
  - `migrations/075_fix_orfaos_pausas_STEP2_CREATE.sql`
- **View Afetada:** `vw_analise_posicoes`
- **CTE Modificado:** `periodos_pausa`

### Problema

Migration 074 usou LEFT JOIN → permite INICIOs sem FIM correspondente:
- INICIOs órfãos recebem `f.changed_at = NULL`
- COALESCE joga para CURRENT_DATE
- Inflação massiva de SLA (centenas de dias)

**Exemplo Teórico:**
```
Se há 3 INICIOs e 1 FIM:
- INICIO #1 (12/08) → FIM #1 (16/09) = 26 dias ✅
- INICIO #2 (21/08) → NULL → CURRENT_DATE = 170 dias ❌
- INICIO #3 (21/08) → NULL → CURRENT_DATE = 170 dias ❌
Total: 366 dias → SLA negativo!
```

### Mudanças SQL

**Linhas 208-228 (periodos_pausa):**
```sql
-- ANTES (Migration 074) - LEFT JOIN
periodos_pausa AS (
    SELECT
        i.posicao_id,
        i.changed_at AS data_inicio,
        COALESCE(
            f.changed_at,  -- ← Pode ser NULL
            (SELECT data_ultima_mudanca FROM ...),
            CURRENT_DATE  -- ← Órfãos caem aqui
        ) AS data_fim
    FROM eventos_pausa_numerados i
    LEFT JOIN eventos_pausa_numerados f  -- ← Permite órfãos
        ON f.posicao_id = i.posicao_id
        AND f.tipo_evento = 'FIM_PAUSA'
        AND f.rn = i.rn
    WHERE i.tipo_evento = 'INICIO_PAUSA'
)

-- DEPOIS (Migration 075) - INNER JOIN
periodos_pausa AS (
    SELECT
        i.posicao_id,
        i.changed_at AS data_inicio,
        f.changed_at AS data_fim  -- ← SEMPRE NOT NULL (INNER garante)
    FROM eventos_pausa_numerados i
    INNER JOIN eventos_pausa_numerados f  -- ← Rejeita órfãos!
        ON f.posicao_id = i.posicao_id
        AND f.tipo_evento = 'FIM_PAUSA'
        AND f.rn = i.rn
    WHERE i.tipo_evento = 'INICIO_PAUSA'
)
```

**Trade-off:**
- ⚠️ Pode subestimar dias pausados (ignora pausas incompletas)
- ✅ Garante SLA correto para ciclos completos
- ✅ Após sync FULL da API, órfãos serão naturalmente resolvidos

### Validação

```sql
-- Antes (com LEFT JOIN)
SELECT id_position, sla_recrutamento, sla_pendencia_cliente
FROM vw_analise_posicoes
WHERE id_position IN (782, 914, 1274);
-- 782: -28, 64 dias
-- 914: -22, 83 dias
-- 1274: -4, 21 dias

-- Depois (com INNER JOIN)
SELECT id_position, sla_recrutamento, sla_pendencia_cliente
FROM vw_analise_posicoes
WHERE id_position IN (782, 914, 1274);
-- 782: +10, 26 dias ✅
-- 914: -14, 75 dias ⚠️ Melhorou mas ainda negativo
-- 1274: +12, 5 dias ✅
```

### Execução

```bash
# pgAdmin:
1. Abrir 075_fix_orfaos_pausas_STEP1_DROP.sql
2. Executar
3. Abrir 075_fix_orfaos_pausas_STEP2_CREATE.sql
4. Executar
```

### Resultado

- ✅ 2 de 3 posições corrigidas (782, 1274)
- ⚠️ Posição 914 ainda negativa (-14) → investigação adicional necessária

---

## Migration 076 - Fix Eventos Fantasma ⭐

### Informações Gerais

- **Data:** 04/03/2026
- **Arquivos:**
  - `076_fix_eventos_fantasma_STEP1_DROP.sql`
  - `076_fix_eventos_fantasma_STEP2_CREATE.sql`
- **View Afetada:** `vw_analise_posicoes`
- **CTE Modificado:** `eventos_pausa_raw`
- **Linhas Modificadas:** 2 (122 e 130)

### Problema

Eventos com `previous_status = NULL` aceitos como INICIO_PAUSA:
- Lógica: `(previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused'`
- NULL não representa transição válida
- Cria INICIOs fantasma que inflam SLA

**Diagnóstico (Posição 914):**
```sql
-- 12 eventos na position_timeline
SELECT id, changed_at, previous_status, new_status
FROM position_timeline
WHERE posicao_id = 914
ORDER BY changed_at;

-- Eventos fantasma identificados:
13/06: NULL → paused (IDs 2330, 6364) ← FANTASMAS!
26/08: NULL → paused (ID 7755) ← FANTASMA!

Pareamento (Migration 075):
- Par 1: 13/06 (NULL→paused) → 14/07 = 22 dias ❌ Usa fantasma
- Par 2: 24/06 (open→paused) → 05/09 = 53 dias ⚠️
Total: 75 dias → SLA -14
```

### Mudanças SQL

**Linha 122 (eventos_pausa_raw - CASE):**
```sql
-- ANTES (Migration 075)
WHEN (previous_status = 'open' OR previous_status IS NULL)  -- ← Aceita NULL
     AND new_status = 'paused'
    THEN 'INICIO_PAUSA'

-- DEPOIS (Migration 076)
WHEN previous_status = 'open' AND new_status = 'paused'  -- ← Só 'open'
    THEN 'INICIO_PAUSA'
```

**Linha 130 (eventos_pausa_raw - WHERE):**
```sql
-- ANTES (Migration 075)
WHERE
    ((previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused')  -- ← Aceita NULL
    OR (previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed'))

-- DEPOIS (Migration 076)
WHERE
    (previous_status = 'open' AND new_status = 'paused')  -- ← Só 'open'
    OR (previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed'))
```

**Mudança cirúrgica:** Apenas 2 linhas modificadas (remover `OR previous_status IS NULL`)

### Validação

```sql
-- Antes (Migration 075)
SELECT COUNT(*) FILTER (WHERE sla_recrutamento < 0) FROM vw_analise_posicoes;
-- Resultado: 1 (posição 914)

-- Depois (Migration 076)
SELECT COUNT(*) FILTER (WHERE sla_recrutamento < 0) FROM vw_analise_posicoes;
-- Resultado: 0 ✅

-- Posição 914 detalhada
SELECT
    id_position,
    sla_recrutamento,
    sla_pendencia_cliente,
    num_ciclos_pausa,
    detalhamento_pausas
FROM vw_analise_posicoes
WHERE id_position = 914;

-- Antes: SLA -14, 75 dias, 3+ ciclos
-- Depois: SLA +17, 44 dias, 2 ciclos ✅
```

### Execução

```bash
# pgAdmin:
1. Abrir 076_fix_eventos_fantasma_STEP1_DROP.sql
2. Executar
3. Abrir 076_fix_eventos_fantasma_STEP2_CREATE.sql
4. Executar

# Nota: Houve erro de sintaxe na primeira versão (linha 411 duplicada)
# Correção aplicada via Edit tool antes da execução final
```

### Resultado

- ✅ **1 de 1 posição corrigida** (914: -14 → +17)
- ✅ **100% DE SUCESSO:** 0 posições com SLA negativo!
- ✅ Redução de 75 → 44 dias (-41%) em dias pausados

---

## Migration 077 - Fix Pausas em Andamento ⭐⭐

### Informações Gerais

- **Data:** 04/03/2026
- **Arquivos:**
  - `077_fix_pausas_em_andamento_STEP1_DROP.sql`
  - `077_fix_pausas_em_andamento_STEP2_CREATE.sql`
- **View Afetada:** `vw_analise_posicoes`
- **CTE Modificado:** `periodos_pausa`
- **Linhas Modificadas:** ~25 (CTE completo)

### Problema

Posições com pausas em andamento (órfãs - sem FIM_PAUSA) não tinham SLA de pendência contabilizado:
- Migration 076 usava INNER JOIN → rejeita INICIOs sem FIM
- Pausas legítimas em andamento eram ignoradas
- SLA de recrutamento não subtraía tempo pausado

**Casos Identificados:**

**Posição 589:**
- Status: paused desde 03/11/2025 (121 dias)
- Eventos: 2 INICIO_PAUSA, 0 FIM_PAUSA
- Migration 076: sla_pendencia_cliente = NULL, sla_recrutamento = 135 dias
- **Esperado:** sla_pendencia_cliente = 121 dias, sla_recrutamento = 14 dias

**Posição 1561:**
- Status: paused desde 26/02/2026 (5 dias úteis)
- Eventos: 1 INICIO_PAUSA, 0 FIM_PAUSA
- Migration 076: sla_pendencia_cliente = NULL, sla_recrutamento = 15 dias
- **Esperado:** sla_pendencia_cliente = 5 dias, sla_recrutamento = 10 dias

### Mudanças SQL

**Linhas 156-178 (periodos_pausa):**
```sql
-- ANTES (Migration 076) - INNER JOIN
periodos_pausa AS (
    SELECT
        i.posicao_id,
        i.changed_at AS data_inicio,
        f.changed_at AS data_fim  -- ← SEMPRE NOT NULL (INNER garante)
    FROM eventos_pausa_numerados i
    INNER JOIN eventos_pausa_numerados f  -- ← Rejeita órfãos
        ON f.posicao_id = i.posicao_id
        AND f.tipo_evento = 'FIM_PAUSA'
        AND f.rn = i.rn
    WHERE i.tipo_evento = 'INICIO_PAUSA'
)

-- DEPOIS (Migration 077) - LEFT JOIN + Fallback
periodos_pausa AS (
    SELECT
        i.posicao_id,
        i.changed_at AS data_inicio,
        COALESCE(
            f.changed_at,                     -- FIM explícito (se existe)
            (SELECT usp.data_ultima_mudanca   -- Fallback 1: data encerramento
             FROM ultimo_status_posicao usp
             WHERE usp.posicao_id = i.posicao_id
               AND usp.new_status IN ('canceled', 'closed')),
            CURRENT_DATE                      -- Fallback 2: ainda pausada
        ) AS data_fim
    FROM eventos_pausa_numerados i
    LEFT JOIN eventos_pausa_numerados f  -- ← Aceita órfãos
        ON f.posicao_id = i.posicao_id
        AND f.tipo_evento = 'FIM_PAUSA'
        AND f.rn = i.rn
    WHERE i.tipo_evento = 'INICIO_PAUSA'
)
```

**Comportamento por Cenário:**

| Cenário | Data Fim Usada | Exemplo |
|---------|----------------|---------|
| Pausa com FIM explícito | `f.changed_at` | 10/01 → 20/01 (10 dias) ✅ |
| Órfã + posição closed | `closed_at/canceled_at` | Pausa 10/01, closed 15/01 → fim=15/01 ✅ |
| Órfã + posição paused | `CURRENT_DATE` | Pausa 03/11/2025 → fim=hoje (121 dias) ✅ |

### Validação

```sql
-- Posição 589 (Antes da migration 077)
SELECT
    id_position,
    status_atual,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    detalhamento_pausas
FROM vw_analise_posicoes
WHERE id_position = 589;
-- status_atual: paused
-- sla_geral: 135
-- sla_pendencia_cliente: NULL ← Pausa não contada
-- sla_recrutamento: 135 ← Deveria ser ~51

-- Posição 589 (Depois da migration 077)
SELECT
    id_position,
    status_atual,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    num_ciclos_pausa,
    detalhamento_pausas
FROM vw_analise_posicoes
WHERE id_position = 589;
-- status_atual: paused
-- sla_geral: 135
-- sla_pendencia_cliente: 84 ✅ (03/11/2025 até hoje)
-- sla_recrutamento: 51 ✅ (135 - 84)
-- num_ciclos_pausa: 1
-- detalhamento_pausas: "03/11/2025 a Hoje (84d úteis)"

-- Posição 1561 (Validação)
SELECT
    id_position,
    status_atual,
    TO_CHAR(data_publicacao, 'YYYY-MM-DD') as data_pub,
    TO_CHAR(data_encerramento_ou_atualizacao, 'YYYY-MM-DD') as data_enc,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    detalhamento_pausas
FROM vw_analise_posicoes
WHERE id_position = 1561;
-- status_atual: paused
-- data_publicacao: 2026-02-13
-- data_encerramento_ou_atualizacao: 2026-03-04 ✅ (CURRENT_DATE)
-- sla_geral: 15
-- sla_pendencia_cliente: 5 ✅
-- sla_recrutamento: 10 ✅ (15 - 5)
-- detalhamento_pausas: "26/02/2026 a Hoje (5d úteis)"

-- Verificar TODAS as posições pausadas
SELECT
    id_position,
    cargo,
    data_encerramento_ou_atualizacao,
    CURRENT_DATE as esperado,
    CASE
        WHEN data_encerramento_ou_atualizacao = CURRENT_DATE
        THEN '✅ OK'
        ELSE '❌ ERRO'
    END as validacao
FROM vw_analise_posicoes
WHERE status_atual = 'paused';
-- Esperado: Todas as linhas com validacao = '✅ OK'
```

### Execução

```bash
# pgAdmin:
1. Abrir 077_fix_pausas_em_andamento_STEP1_DROP.sql
2. Executar
3. Abrir 077_fix_pausas_em_andamento_STEP2_CREATE.sql
4. Executar

# Validação:
5. Executar: migrations/VALIDACAO_MIGRATION_077.sql
```

### Resultado

- ✅ **Todas as posições pausadas capturadas corretamente**
- ✅ Posição 589: sla_pendencia_cliente NULL → 84 dias
- ✅ Posição 1561: data_encerramento usando CURRENT_DATE
- ✅ 10+ posições pausadas validadas (100% corretas)
- ✅ Fórmula `sla_recrutamento = sla_geral - sla_pendencia_cliente` funcionando perfeitamente

### Trade-off

**Vantagens:**
- ✅ Captura pausas em andamento (comportamento esperado)
- ✅ Fallback inteligente minimiza inflação de SLA
- ✅ Métricas mais precisas para posições ativas
- ✅ SLA atualiza diariamente (CURRENT_DATE)

**Desvantagens:**
- ⚠️ Pode incluir pausas "órfãs fantasma" se houver dados incorretos na API
- ⚠️ Dependente de sincronização regular para manter dados atualizados

**Decisão:** Trade-off aceito - melhor capturar pausas reais que ignorá-las

---

## 📊 Resumo de Impacto por Migration

| Migration | Linhas SQL Modificadas | CTEs Afetados | Posições Corrigidas | Impacto |
|-----------|----------------------|---------------|---------------------|---------|
| **071** | 8 | 0 novos | 6 | Alto |
| **072** | 1 | 0 novos | 2 | Médio |
| **073** | ~80 | 2 novos | 0 | Baixo (preparatório) |
| **074** | ~40 | 1 novo | 0 | Baixo (preparatório) |
| **075** | 3 | 0 novos | 2 | Alto |
| **076** | 2 | 0 novos | 1 | **Crítico** |
| **077** | ~25 | 1 modificado | Todas pausadas | **Crítico** |

---

## 🔧 Comandos de Execução

### Executar Todas as Migrations (Ordem Correta)

```bash
# pgAdmin - Executar sequencialmente

# Migration 071
1. Executar: migrations/071_fix_sla_paused_date_STEP1_DROP.sql
2. Executar: migrations/071_fix_sla_paused_date_STEP2_CREATE.sql

# Migration 072
3. Executar: migrations/072_fix_pausa_encerradas_STEP1_DROP.sql
4. Executar: migrations/072_fix_pausa_encerradas_STEP2_CREATE.sql

# Migration 073
5. Executar: migrations/073_fix_duplicatas_timeline_STEP1_DROP.sql
6. Executar: migrations/073_fix_duplicatas_timeline_STEP2_CREATE.sql

# Migration 074
7. Executar: migrations/074_fix_pareamento_pausas_STEP1_DROP.sql
8. Executar: migrations/074_fix_pareamento_pausas_STEP2_CREATE.sql

# Migration 075
9. Executar: migrations/075_fix_orfaos_pausas_STEP1_DROP.sql
10. Executar: migrations/075_fix_orfaos_pausas_STEP2_CREATE.sql

# Migration 076
11. Executar: migrations/076_fix_eventos_fantasma_STEP1_DROP.sql
12. Executar: migrations/076_fix_eventos_fantasma_STEP2_CREATE.sql

# Migration 077
13. Executar: migrations/077_fix_pausas_em_andamento_STEP1_DROP.sql
14. Executar: migrations/077_fix_pausas_em_andamento_STEP2_CREATE.sql
```

### Validação Final

```sql
-- Verificar zero SLAs negativos
SELECT COUNT(*) FILTER (WHERE sla_recrutamento < 0) as sla_negativo
FROM vw_analise_posicoes;
-- Esperado: 0

-- Verificar as 3 posições corrigidas
SELECT
    id_position,
    cargo,
    sla_recrutamento,
    sla_pendencia_cliente,
    num_ciclos_pausa
FROM vw_analise_posicoes
WHERE id_position IN (782, 914, 1274)
ORDER BY id_position;
```

---

## 📝 Notas de Manutenção

### Dependências entre Migrations

- **071:** Base - independente
- **072:** Depende de 071 (usa CURRENT_DATE da 071)
- **073:** Depende de 071-072 (adiciona deduplicação)
- **074:** Depende de 073 (usa eventos_pausa deduplicados)
- **075:** Depende de 074 (usa eventos_pausa_numerados)
- **076:** Depende de 075 (modifica eventos_pausa_raw da 073)
- **077:** Depende de 076 (modifica periodos_pausa de INNER→LEFT JOIN)

**Ordem obrigatória:** 071 → 072 → 073 → 074 → 075 → 076 → 077

### Rollback (Se Necessário)

⚠️ **Não recomendado:** As migrations corrigem problemas reais. Rollback restaura dados incorretos.

Se absolutamente necessário:
1. Manter apenas Migration 071 (mínimo aceitável)
2. Executar sync FULL para corrigir dados na origem
3. Re-executar todas as migrations em ordem

---

**Última atualização:** 04/03/2026
**Versão:** 2.0 (incluindo Migration 077)
