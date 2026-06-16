# Guia de Manutenção e Monitoramento de SLAs

**Data de Criação:** 2026-03-04
**Versão:** 1.1
**Última Atualização:** 2026-03-04 (Migration 077)

---

## 📋 Sumário

1. [Introdução](#introdução)
2. [Queries de Monitoramento](#queries-de-monitoramento)
3. [Troubleshooting](#troubleshooting)
4. [Problemas Comuns](#problemas-comuns)
5. [Sistema de Alertas](#sistema-de-alertas)
6. [Procedimentos de Emergência](#procedimentos-de-emergência)
7. [Manutenção Preventiva](#manutenção-preventiva)
8. [Referências](#referências)

---

## 🎯 Introdução

Este guia fornece procedimentos e queries para monitoramento e manutenção dos cálculos de SLA na view `vw_analise_posicoes`.

### O Que São os SLAs?

A view calcula três métricas principais:

1. **sla_geral**: Dias úteis totais desde abertura até encerramento/hoje
2. **sla_pendencia_cliente**: Dias úteis que a posição ficou em status `paused`
3. **sla_recrutamento**: `sla_geral - sla_pendencia_cliente` (tempo efetivo de recrutamento)

### Indicadores de Saúde

✅ **Saudável:**
- sla_recrutamento >= 0
- sla_pendencia_cliente <= sla_geral
- num_ciclos_pausa coerente com detalhamento_pausas

🟡 **Atenção:**
- sla_recrutamento < 10 mas >= 0
- num_ciclos_pausa > 10 (muitas pausas)
- sla_pendencia_cliente > 100 dias (pausa muito longa)

🔴 **Crítico:**
- sla_recrutamento < 0 ← **NUNCA deve acontecer**
- sla_pendencia_cliente > sla_geral ← **Erro matemático**
- Ciclos de pausa sem datas

---

## 📊 Queries de Monitoramento

### 1. Verificar SLAs Negativos (Query Diária)

```sql
-- ⚠️ EXECUTAR DIARIAMENTE
-- Deve retornar 0 linhas sempre!

SELECT
    id_position,
    cargo,
    status_atual,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    num_ciclos_pausa,
    LEFT(detalhamento_pausas, 200) as pausas
FROM vw_analise_posicoes
WHERE sla_recrutamento < 0
ORDER BY sla_recrutamento ASC;
```

**Resultado Esperado:** `0 linhas`

**Se retornar linhas:**
1. Copiar IDs das posições
2. Executar diagnóstico completo (seção 3)
3. Abrir ticket de investigação
4. Não executar sync até resolver

---

### 2. Distribuição de SLAs (Query Semanal)

```sql
-- Visão geral da saúde dos SLAs
-- Executar 1x por semana

SELECT
    CASE
        WHEN sla_recrutamento < 0 THEN '🔴 Negativo (ERRO!)'
        WHEN sla_recrutamento BETWEEN 0 AND 10 THEN '🟡 Muito Baixo (0-10 dias)'
        WHEN sla_recrutamento BETWEEN 11 AND 30 THEN '🟢 Baixo (11-30 dias)'
        WHEN sla_recrutamento BETWEEN 31 AND 60 THEN '🟢 Médio (31-60 dias)'
        WHEN sla_recrutamento BETWEEN 61 AND 90 THEN '🟡 Alto (61-90 dias)'
        ELSE '🔴 Muito Alto (>90 dias)'
    END as faixa_sla,
    COUNT(*) as total_posicoes,
    ROUND(AVG(sla_recrutamento), 1) as media_sla,
    MIN(sla_recrutamento) as min_sla,
    MAX(sla_recrutamento) as max_sla
FROM vw_analise_posicoes
GROUP BY
    CASE
        WHEN sla_recrutamento < 0 THEN '🔴 Negativo (ERRO!)'
        WHEN sla_recrutamento BETWEEN 0 AND 10 THEN '🟡 Muito Baixo (0-10 dias)'
        WHEN sla_recrutamento BETWEEN 11 AND 30 THEN '🟢 Baixo (11-30 dias)'
        WHEN sla_recrutamento BETWEEN 31 AND 60 THEN '🟢 Médio (31-60 dias)'
        WHEN sla_recrutamento BETWEEN 61 AND 90 THEN '🟡 Alto (61-90 dias)'
        ELSE '🔴 Muito Alto (>90 dias)'
    END
ORDER BY min_sla ASC;
```

**Exemplo de Resultado Saudável:**
```
faixa_sla                        | total_posicoes | media_sla | min_sla | max_sla
---------------------------------+----------------+-----------+---------+---------
🟢 Muito Baixo (0-10 dias)       |            123 |       5.2 |       0 |      10
🟢 Baixo (11-30 dias)            |            456 |      22.1 |      11 |      30
🟢 Médio (31-60 dias)            |            789 |      45.3 |      31 |      60
```

**🔴 Atenção se:**
- Aparecer linha com "Negativo (ERRO!)"
- Mais de 10% das posições em "Muito Alto"

---

### 3. Verificar Coerência Matemática (Query Diária)

```sql
-- sla_recrutamento DEVE SER = sla_geral - sla_pendencia_cliente
-- Tolerância: ±1 dia (arredondamentos)

SELECT
    id_position,
    cargo,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    (sla_geral - sla_pendencia_cliente) as calculado,
    ABS(sla_recrutamento - (sla_geral - sla_pendencia_cliente)) as diferenca
FROM vw_analise_posicoes
WHERE ABS(sla_recrutamento - (sla_geral - sla_pendencia_cliente)) > 1
ORDER BY diferenca DESC
LIMIT 20;
```

**Resultado Esperado:** `0 linhas` ou diferenças <= 1

**Se retornar linhas:**
- Verificar se há problemas na lógica da view
- Possível bug em calcular_dias_uteis()

---

### 4. Detectar Ciclos de Pausa Órfãos em Posições Encerradas (Query Semanal)

```sql
-- Pausas sem data de fim quando posição já foi encerrada
-- Pode inflar SLA artificialmente (corrigido pela Migration 077)

SELECT
    id_position,
    cargo,
    status_atual,
    num_ciclos_pausa,
    detalhamento_pausas
FROM vw_analise_posicoes
WHERE status_atual IN ('canceled', 'closed')
  AND detalhamento_pausas LIKE '%até hoje%'
ORDER BY id_position;
```

**Resultado Esperado:** `0 linhas` (após Migration 077)

**Se retornar linhas:**
- Indica falta de FIM_PAUSA para posições encerradas
- Migration 077 deveria usar data de encerramento como fallback
- Executar diagnóstico de eventos fantasma (seção 3.4)

---

### 5. Monitorar Pausas em Andamento (Query Diária - NOVO)

```sql
-- Posições atualmente pausadas (status paused) com pausas em andamento
-- Migration 077 usa CURRENT_DATE para calcular SLA até hoje
-- ⚠️ É ESPERADO que estas posições tenham "até hoje" no detalhamento

SELECT
    id_position,
    cargo,
    status_atual,
    TO_CHAR(data_publicacao, 'DD/MM/YYYY') as data_abertura,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    num_ciclos_pausa,
    LEFT(detalhamento_pausas, 200) as pausas
FROM vw_analise_posicoes
WHERE status_atual = 'paused'
  AND detalhamento_pausas LIKE '%até hoje%'
ORDER BY sla_pendencia_cliente DESC;
```

**Resultado Típico:** Algumas linhas (posições pausadas atualmente)

**✅ Comportamento Esperado:**
- Posições com `status_atual = 'paused'` DEVEM ter "até hoje"
- `sla_pendencia_cliente` aumenta 1 dia útil por dia
- `sla_recrutamento` permanece estável (não conta dias pausados)

**🔴 Atenção se:**
- `sla_pendencia_cliente > 200` dias (pausa muito longa, revisar com negócio)
- `num_ciclos_pausa > 5` (muitas pausas, pode indicar problema no processo)
- Posição pausada há >6 meses (pode estar esquecida)

---

### 6. Monitorar Pausas Excessivas (Query Semanal)

```sql
-- Posições com mais de 5 ciclos de pausa (pode indicar dados duplicados)

SELECT
    id_position,
    cargo,
    status_atual,
    num_ciclos_pausa,
    sla_pendencia_cliente,
    LEFT(detalhamento_pausas, 300) as pausas
FROM vw_analise_posicoes
WHERE num_ciclos_pausa > 5
ORDER BY num_ciclos_pausa DESC, sla_pendencia_cliente DESC
LIMIT 20;
```

**Resultado Típico:** Algumas linhas (posições complexas)

**🔴 Atenção se:**
- num_ciclos_pausa > 10 (investigar duplicatas)
- sla_pendencia_cliente > 200 dias (pausa excessiva)

---

### 7. Verificar Eventos Fantasma (Query Mensal)

```sql
-- Eventos com previous_status = NULL
-- Após Migration 076, NÃO devem contar como INICIO_PAUSA

SELECT
    p.id,
    p.inhire_id,
    p.status,
    COUNT(*) FILTER (WHERE pt.previous_status IS NULL) as eventos_com_null,
    COUNT(*) as total_eventos
FROM posicoes p
LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
GROUP BY p.id, p.inhire_id, p.status
HAVING COUNT(*) FILTER (WHERE pt.previous_status IS NULL) > 0
ORDER BY eventos_com_null DESC
LIMIT 50;
```

**Resultado:** Pode ter linhas (eventos NULL existem no histórico)

**✅ Verificar:**
- Se esses eventos NULL estão sendo classificados como INICIO_PAUSA
- Se sim, Migration 076 não foi aplicada corretamente

**Query de Validação:**
```sql
-- Verificar se eventos NULL estão classificados como INICIO_PAUSA
-- (não devem estar após Migration 076)

WITH eventos_pausa_raw AS (
    SELECT
        pt.posicao_id,
        pt.previous_status,
        pt.new_status,
        CASE
            WHEN previous_status = 'open' AND new_status = 'paused'
                THEN 'INICIO_PAUSA'
            WHEN previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed')
                THEN 'FIM_PAUSA'
            ELSE NULL
        END as tipo_evento
    FROM position_timeline pt
)
SELECT
    COUNT(*) as eventos_null_classificados_como_inicio
FROM eventos_pausa_raw
WHERE previous_status IS NULL
  AND tipo_evento = 'INICIO_PAUSA';
```

**Resultado Esperado:** `0` (após Migration 076)

---

### 8. Auditoria de Position Timeline (Query sob Demanda)

```sql
-- Para investigar posição específica
-- Substituir {POSITION_ID} pelo ID da posição

WITH eventos AS (
    SELECT
        pt.id,
        pt.posicao_id,
        TO_CHAR(pt.changed_at, 'DD/MM/YYYY HH24:MI:SS') as data_hora,
        COALESCE(pt.previous_status, 'NULL') as status_anterior,
        pt.new_status as status_novo,
        CASE
            WHEN pt.previous_status = 'open' AND pt.new_status = 'paused'
                THEN 'INICIO_PAUSA'
            WHEN pt.previous_status = 'paused' AND pt.new_status IN ('open', 'canceled', 'closed')
                THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END as classificacao,
        CASE WHEN pt.notes IS NOT NULL AND pt.notes != '' THEN '✓' ELSE '' END as tem_notes
    FROM position_timeline pt
    WHERE pt.posicao_id = {POSITION_ID}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY data_hora) as seq,
    id,
    data_hora,
    status_anterior || ' → ' || status_novo as transicao,
    classificacao,
    tem_notes
FROM eventos
ORDER BY data_hora, id;
```

**Uso:**
1. Substituir `{POSITION_ID}` pelo ID da posição problemática
2. Verificar sequência de eventos
3. Identificar duplicatas, eventos NULL, ou sequências inválidas

**Padrão Esperado:**
```
seq | transicao        | classificacao
----+------------------+--------------
1   | NULL → open      | OUTRO
2   | open → paused    | INICIO_PAUSA
3   | paused → open    | FIM_PAUSA
4   | open → paused    | INICIO_PAUSA
5   | paused → closed  | FIM_PAUSA
```

**🔴 Atenção:**
- `NULL → paused` classificado como INICIO_PAUSA (fantasma!)
- Múltiplos `INICIO_PAUSA` sem `FIM_PAUSA` (órfão!)
- Eventos com mesma data/hora (duplicata!)

---

## 🔧 Troubleshooting

### 3.1 SLA Recrutamento Negativo

**Sintoma:**
```sql
id_position: 914
sla_geral: 61
sla_pendencia_cliente: 75
sla_recrutamento: -14  ← ERRO!
```

**Diagnóstico Passo a Passo:**

#### Passo 1: Verificar Eventos da Posição

```sql
SELECT
    pt.id,
    TO_CHAR(pt.changed_at, 'DD/MM/YYYY HH24:MI:SS') as data,
    COALESCE(pt.previous_status, 'NULL') as anterior,
    pt.new_status as novo,
    CASE
        WHEN pt.previous_status = 'open' AND pt.new_status = 'paused'
            THEN 'INICIO_PAUSA'
        WHEN pt.previous_status = 'paused' AND pt.new_status IN ('open', 'canceled', 'closed')
            THEN 'FIM_PAUSA'
        ELSE 'OUTRO'
    END as tipo
FROM position_timeline pt
WHERE pt.posicao_id = (
    SELECT id FROM posicoes WHERE id = 914  -- Substituir pelo ID problemático
)
ORDER BY pt.changed_at, pt.id;
```

#### Passo 2: Identificar o Problema

Compare o resultado com os padrões conhecidos:

**Problema A: Eventos Fantasma (NULL → paused)**
```
NULL → paused  ← Classificado como INICIO_PAUSA (errado!)
```
**Solução:** Aplicar Migration 076

**Problema B: Órfãos (INICIO sem FIM)**
```
open → paused    (INICIO_PAUSA)
open → paused    (INICIO_PAUSA)
paused → closed  (FIM_PAUSA)
```
**Solução:** Aplicar Migration 075 (INNER JOIN)

**Problema C: Duplicatas**
```
open → paused  (ID 1234, 12:30:15)
open → paused  (ID 5678, 12:30:15)  ← Mesmo timestamp
```
**Solução:** Aplicar Migration 073 (DISTINCT ON)

**Problema D: Pausa Continua Após Encerramento**
```
open → paused    (01/01/2025)
posição cancelada (10/01/2025)
pausa conta até hoje (04/03/2026)  ← 420 dias!
```
**Solução:** Aplicar Migration 072

#### Passo 3: Aplicar a Correção

Consultar documentação da migration correspondente:
- `migrations/MIGRATION_071_077_CHANGELOG.md`

Executar STEP1 (DROP) e STEP2 (CREATE) em sequência.

#### Passo 4: Validar Correção

```sql
SELECT
    id_position,
    cargo,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    num_ciclos_pausa
FROM vw_analise_posicoes
WHERE id_position = 914;  -- Substituir pelo ID corrigido
```

**Resultado Esperado:**
- sla_recrutamento >= 0
- sla_pendencia_cliente <= sla_geral

---

### 3.2 SLA Pendência Cliente Maior que SLA Geral

**Sintoma:**
```sql
sla_geral: 50
sla_pendencia_cliente: 65  ← Impossível!
```

**Causa Provável:**
- Pausas órfãs (INICIO sem FIM) → conta até hoje
- Eventos duplicados inflando contagem

**Diagnóstico:**

```sql
-- Ver detalhamento das pausas
SELECT
    id_position,
    cargo,
    status_atual,
    data_publicacao,
    data_encerramento_ou_atualizacao,
    sla_geral,
    sla_pendencia_cliente,
    num_ciclos_pausa,
    detalhamento_pausas
FROM vw_analise_posicoes
WHERE sla_pendencia_cliente > sla_geral;
```

Verificar `detalhamento_pausas`:
- Se aparecer `até hoje` → Pausa órfã
- Se datas ultrapassam `data_encerramento_ou_atualizacao` → Migration 072

**Solução:**
- Aplicar Migration 077 (usa LEFT JOIN com fallback inteligente)
- Migration 077 substitui 075 (INNER JOIN) e melhora 072

---

### 3.3 Número de Ciclos de Pausa Muito Alto

**Sintoma:**
```sql
num_ciclos_pausa: 25  ← Excessivo!
```

**Causa Provável:**
- Eventos duplicados na position_timeline
- Sincronizações múltiplas criando registros repetidos

**Diagnóstico:**

```sql
-- Verificar duplicatas
SELECT
    posicao_id,
    changed_at,
    previous_status,
    new_status,
    COUNT(*) as qtd_duplicatas
FROM position_timeline
WHERE posicao_id = (SELECT id FROM posicoes WHERE id = 123)  -- ID problemático
GROUP BY posicao_id, changed_at, previous_status, new_status
HAVING COUNT(*) > 1
ORDER BY changed_at;
```

**Solução:**
- Aplicar Migration 073 (DISTINCT ON)
- Se persistir, considerar limpeza manual na tabela

---

### 3.4 Pausas "até hoje" em Posições Encerradas

**Sintoma:**
```sql
status_atual: canceled
detalhamento_pausas: "Ciclo 1: 15/01/2025 até hoje (45 dias)"
data_encerramento_ou_atualizacao: 20/01/2025
```

**Problema:** Pausa conta 45 dias, mas posição foi cancelada após 5 dias

**Diagnóstico:**

```sql
-- Verificar se há FIM_PAUSA após encerramento
SELECT
    p.id,
    p.status,
    p.hired_at,
    p.canceled_at,
    p.closed_at,
    MAX(pt.changed_at) FILTER (WHERE pt.new_status = 'paused') as ultimo_inicio_pausa,
    MAX(pt.changed_at) FILTER (WHERE pt.previous_status = 'paused') as ultimo_fim_pausa
FROM posicoes p
LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
WHERE p.id = 123  -- ID problemático
GROUP BY p.id, p.status, p.hired_at, p.canceled_at, p.closed_at;
```

**Se ultimo_fim_pausa IS NULL:**
- Pausa nunca foi finalizada
- Aplicar Migration 072 (usa data de encerramento como fim)

**Se ultimo_fim_pausa > data_encerramento:**
- Timeline inconsistente
- Pode precisar limpeza manual

---

## 🚨 Problemas Comuns

### Problema 1: Sincronização Cria Eventos Duplicados

**Sintomas:**
- Múltiplos eventos com mesmo timestamp
- `num_ciclos_pausa` aumenta após cada sync

**Causa:**
- Sincronização incremental não verifica duplicatas antes de inserir

**Solução Imediata:**
```sql
-- Aplicar Migration 073 (deduplicação automática na view)
\i migrations/073_fix_duplicatas_timeline_STEP1_DROP.sql
\i migrations/073_fix_duplicatas_timeline_STEP2_CREATE.sql
```

**Prevenção:**
- Adicionar constraint UNIQUE na tabela position_timeline:
```sql
ALTER TABLE position_timeline
ADD CONSTRAINT uq_position_timeline_evento
UNIQUE (posicao_id, changed_at, previous_status, new_status);
```

---

### Problema 2: Eventos com previous_status = NULL

**Sintomas:**
- SLAs negativos após sincronização
- Eventos classificados como INICIO_PAUSA sem transição válida

**Causa:**
- API Inhire retorna eventos sem status anterior
- Sincronizações retroativas

**Identificar:**
```sql
SELECT
    COUNT(*) as total_eventos_null,
    COUNT(DISTINCT posicao_id) as posicoes_afetadas
FROM position_timeline
WHERE previous_status IS NULL;
```

**Solução:**
- Migration 076 rejeita esses eventos como INICIO_PAUSA
- Migration 077 mantém essa correção
- Aplicar migration mais recente:
```sql
\i migrations/077_fix_pausas_em_andamento_STEP1_DROP.sql
\i migrations/077_fix_pausas_em_andamento_STEP2_CREATE.sql
```

---

### Problema 3: Posição Pausada Há Muito Tempo

**Sintomas:**
```sql
status_atual: paused
sla_pendencia_cliente: 500  ← 500 dias!
```

**Causa:**
- Posição realmente pausada há muito tempo (não é bug)
- OU falta evento de FIM_PAUSA

**Diagnóstico:**

```sql
-- Verificar última mudança na API
SELECT
    p.id,
    p.inhire_id,
    p.status,
    p.updated_at_inhire as ultima_atualizacao_api,
    MAX(pt.changed_at) as ultimo_evento_timeline
FROM posicoes p
LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
WHERE p.id = 123
GROUP BY p.id, p.inhire_id, p.status, p.updated_at_inhire;
```

**Se ultima_atualizacao_api < ultimo_evento_timeline:**
- Dados do BD mais recentes que API (estranho!)
- Executar sync completa

**Se ultima_atualizacao_api é recente:**
- Posição realmente pausada há muito tempo (válido)
- Revisar com equipe de negócio

---

### Problema 4: SLA Zerado Indevidamente

**Sintomas:**
```sql
sla_recrutamento: 0
data_publicacao: 01/01/2025
data_encerramento_ou_atualizacao: 15/03/2025  ← 74 dias depois!
```

**Causa:**
- Todos os dias contados como pendência_cliente
- Posição ficou 100% do tempo pausada

**Diagnóstico:**

```sql
SELECT
    id_position,
    cargo,
    data_publicacao,
    data_encerramento_ou_atualizacao,
    sla_geral,
    sla_pendencia_cliente,
    sla_recrutamento,
    detalhamento_pausas
FROM vw_analise_posicoes
WHERE sla_recrutamento = 0
  AND sla_geral > 0;
```

**Verificar:**
- Se `sla_pendencia_cliente = sla_geral` → Posição 100% pausada (pode ser válido)
- Se `detalhamento_pausas` cobre todo o período → OK
- Se não cobre → Investigar eventos

---

## 🔔 Sistema de Alertas

### Alertas Críticos (Executar Diariamente)

Criar script `scripts/monitoramento/check_sla_health.sql`:

```sql
-- ALERTA 1: SLAs Negativos (NUNCA deve acontecer)
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM vw_analise_posicoes
    WHERE sla_recrutamento < 0;

    IF v_count > 0 THEN
        RAISE WARNING '🔴 ALERTA CRÍTICO: % posições com SLA negativo!', v_count;
    ELSE
        RAISE NOTICE '✅ OK: Nenhuma posição com SLA negativo';
    END IF;
END $$;

-- ALERTA 2: Inconsistência Matemática
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM vw_analise_posicoes
    WHERE ABS(sla_recrutamento - (sla_geral - sla_pendencia_cliente)) > 1;

    IF v_count > 0 THEN
        RAISE WARNING '🔴 ALERTA: % posições com inconsistência matemática!', v_count;
    ELSE
        RAISE NOTICE '✅ OK: Cálculos matemáticos consistentes';
    END IF;
END $$;

-- ALERTA 3: Pausas Órfãs em Posições Encerradas
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM vw_analise_posicoes
    WHERE status_atual IN ('canceled', 'closed')
      AND detalhamento_pausas LIKE '%até hoje%';

    IF v_count > 0 THEN
        RAISE WARNING '🟡 ALERTA: % posições encerradas com pausas órfãs!', v_count;
    ELSE
        RAISE NOTICE '✅ OK: Nenhuma pausa órfã em posições encerradas';
    END IF;
END $$;
```

**Executar:**
```bash
psql -U postgres -d inhire -f scripts/monitoramento/check_sla_health.sql
```

**Automatizar (cron):**
```bash
# Executar diariamente às 09:00
0 9 * * * psql -U postgres -d inhire -f /path/to/scripts/monitoramento/check_sla_health.sql 2>&1 | mail -s "SLA Health Check" admin@empresa.com
```

---

### Alertas de Atenção (Executar Semanalmente)

```sql
-- ALERTA 4: Muitas Pausas
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM vw_analise_posicoes
    WHERE num_ciclos_pausa > 10;

    IF v_count > 0 THEN
        RAISE WARNING '🟡 ATENÇÃO: % posições com mais de 10 ciclos de pausa', v_count;
    END IF;
END $$;

-- ALERTA 5: Pausas Muito Longas
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM vw_analise_posicoes
    WHERE sla_pendencia_cliente > 200;

    IF v_count > 0 THEN
        RAISE WARNING '🟡 ATENÇÃO: % posições com mais de 200 dias em pausa', v_count;
    END IF;
END $$;
```

---

## 🚑 Procedimentos de Emergência

### Emergência 1: SLAs Negativos Após Sincronização

**Ação Imediata:**

1. **Parar sincronizações automáticas**
```bash
# Desabilitar cron
crontab -e
# Comentar linha de sync
```

2. **Identificar posições afetadas**
```sql
SELECT id_position, cargo, sla_recrutamento
FROM vw_analise_posicoes
WHERE sla_recrutamento < 0;
```

3. **Executar diagnóstico completo** (seção 3.1)

4. **Aplicar migration corretiva** (conforme diagnóstico)

5. **Validar correção**
```sql
SELECT COUNT(*) FROM vw_analise_posicoes WHERE sla_recrutamento < 0;
-- Deve retornar 0
```

6. **Reativar sincronizações**

---

### Emergência 2: View Não Atualiza Após Sync

**Sintomas:**
- Sync executou com sucesso
- View ainda mostra dados antigos

**Diagnóstico:**

```sql
-- Comparar timestamps
SELECT
    'posicoes' as tabela,
    MAX(updated_at_inhire) as ultima_atualizacao_api
FROM posicoes
UNION ALL
SELECT
    'position_timeline',
    MAX(changed_at)
FROM position_timeline
UNION ALL
SELECT
    'view',
    MAX(data_publicacao)
FROM vw_analise_posicoes;
```

**Causa Provável:**
- View precisa ser recriada (DROP/CREATE)

**Solução:**

```sql
-- Recriar view manualmente (usar migration mais recente)
\i migrations/077_fix_pausas_em_andamento_STEP1_DROP.sql
\i migrations/077_fix_pausas_em_andamento_STEP2_CREATE.sql
```

---

### Emergência 3: Performance Degradada

**Sintomas:**
- Queries na view demorando >30 segundos
- Timeout em dashboards

**Diagnóstico:**

```sql
EXPLAIN ANALYZE
SELECT * FROM vw_analise_posicoes
WHERE id_position = 123;
```

**Soluções Possíveis:**

1. **Reindexar tabelas**
```sql
REINDEX TABLE position_timeline;
REINDEX TABLE posicoes;
```

2. **Atualizar estatísticas**
```sql
ANALYZE position_timeline;
ANALYZE posicoes;
ANALYZE candidaturas;
```

3. **Verificar locks**
```sql
SELECT
    pid,
    state,
    query_start,
    LEFT(query, 50) as query
FROM pg_stat_activity
WHERE datname = 'inhire'
  AND state != 'idle'
ORDER BY query_start;
```

4. **Matar processos travados** (cuidado!)
```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'inhire'
  AND state = 'idle in transaction'
  AND query_start < NOW() - INTERVAL '10 minutes';
```

---

## 🛡️ Manutenção Preventiva

### Rotina Diária

```bash
#!/bin/bash
# scripts/monitoramento/daily_check.sh

echo "=== Check SLA Diário - $(date) ==="

# 1. Verificar SLAs negativos
psql -U postgres -d inhire -t -c "
SELECT COUNT(*) FROM vw_analise_posicoes WHERE sla_recrutamento < 0;
" | while read count; do
    if [ "$count" -gt 0 ]; then
        echo "🔴 ALERTA: $count posições com SLA negativo!"
        # Enviar email/Slack
    else
        echo "✅ OK: Nenhum SLA negativo"
    fi
done

# 2. Verificar última sincronização
psql -U postgres -d inhire -t -c "
SELECT
    EXTRACT(EPOCH FROM (NOW() - MAX(start_time)))/3600 as horas
FROM sync_log
WHERE sync_type = 'INCREMENTAL';
" | while read horas; do
    if (( $(echo "$horas > 4" | bc -l) )); then
        echo "🟡 ATENÇÃO: Última sync há $horas horas"
    else
        echo "✅ OK: Sync recente"
    fi
done

echo "=== Fim do Check ==="
```

**Agendar:**
```bash
# crontab
0 9 * * * /path/to/scripts/monitoramento/daily_check.sh >> /var/log/sla_check.log 2>&1
```

---

### Rotina Semanal

```sql
-- scripts/monitoramento/weekly_report.sql

\echo '=== RELATÓRIO SEMANAL DE SLAs ==='
\echo ''

-- Resumo Geral
\echo '1. RESUMO GERAL'
SELECT
    COUNT(*) as total_posicoes,
    COUNT(*) FILTER (WHERE sla_recrutamento < 0) as slas_negativos,
    ROUND(AVG(sla_recrutamento), 1) as media_sla_recrutamento,
    ROUND(AVG(sla_pendencia_cliente), 1) as media_pendencia_cliente,
    MAX(sla_recrutamento) as max_sla
FROM vw_analise_posicoes;

\echo ''
\echo '2. DISTRIBUIÇÃO POR STATUS'
SELECT
    status_atual,
    COUNT(*) as total,
    ROUND(AVG(sla_recrutamento), 1) as media_sla
FROM vw_analise_posicoes
GROUP BY status_atual
ORDER BY total DESC;

\echo ''
\echo '3. TOP 10 MAIORES SLAs DE PENDÊNCIA'
SELECT
    id_position,
    cargo,
    sla_pendencia_cliente,
    num_ciclos_pausa
FROM vw_analise_posicoes
ORDER BY sla_pendencia_cliente DESC
LIMIT 10;

\echo ''
\echo '4. POSIÇÕES COM MUITOS CICLOS DE PAUSA'
SELECT
    COUNT(*) as total,
    AVG(num_ciclos_pausa) as media_ciclos
FROM vw_analise_posicoes
WHERE num_ciclos_pausa > 5;
```

**Executar:**
```bash
psql -U postgres -d inhire -f scripts/monitoramento/weekly_report.sql > reports/sla_$(date +%Y%m%d).txt
```

---

### Rotina Mensal

1. **Backup da view**
```bash
pg_dump -U postgres -d inhire -t vw_analise_posicoes --schema-only > backups/vw_analise_posicoes_$(date +%Y%m).sql
```

2. **Auditoria de eventos fantasma**
```sql
-- Ver se eventos NULL estão aumentando
SELECT
    DATE_TRUNC('month', changed_at) as mes,
    COUNT(*) FILTER (WHERE previous_status IS NULL) as eventos_null,
    COUNT(*) as total_eventos,
    ROUND(100.0 * COUNT(*) FILTER (WHERE previous_status IS NULL) / COUNT(*), 2) as percentual
FROM position_timeline
GROUP BY DATE_TRUNC('month', changed_at)
ORDER BY mes DESC
LIMIT 12;
```

3. **Análise de tendências**
```sql
-- SLA médio por mês de publicação
SELECT
    TO_CHAR(data_publicacao, 'YYYY-MM') as mes_publicacao,
    COUNT(*) as total_posicoes,
    ROUND(AVG(sla_recrutamento), 1) as media_sla_recrutamento,
    ROUND(AVG(sla_pendencia_cliente), 1) as media_pendencia_cliente
FROM vw_analise_posicoes
WHERE data_publicacao >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY TO_CHAR(data_publicacao, 'YYYY-MM')
ORDER BY mes_publicacao DESC;
```

---

## 📚 Referências

### Documentação Relacionada

1. **Relatório de Correção de SLAs**
   - `docs/reports/RELATORIO_CORRECAO_SLAS_2026-03-04.md`
   - Histórico completo das 7 migrations (071-077)

2. **Changelog de Migrations**
   - `migrations/MIGRATION_071_077_CHANGELOG.md`
   - Detalhes técnicos de cada correção

3. **Migrations Aplicadas**
   - `migrations/071_*` a `migrations/077_*`
   - Scripts DROP e CREATE

4. **Validação de Migrations**
   - `migrations/VALIDACAO_MIGRATION_077.sql`
   - 8 queries de validação para Migration 077

### Queries de Referência

```sql
-- Template para investigar posição específica
WITH info_posicao AS (
    SELECT
        p.id,
        p.inhire_id,
        p.status,
        p.opened_at,
        p.hired_at,
        p.canceled_at,
        p.closed_at,
        v.sla_geral,
        v.sla_pendencia_cliente,
        v.sla_recrutamento,
        v.num_ciclos_pausa,
        v.detalhamento_pausas
    FROM posicoes p
    LEFT JOIN vw_analise_posicoes v ON p.id = v.id_position
    WHERE p.id = {POSITION_ID}
),
eventos AS (
    SELECT
        pt.id,
        TO_CHAR(pt.changed_at, 'DD/MM/YYYY HH24:MI:SS') as data_hora,
        COALESCE(pt.previous_status, 'NULL') as anterior,
        pt.new_status as novo,
        pt.notes
    FROM position_timeline pt
    WHERE pt.posicao_id = {POSITION_ID}
    ORDER BY pt.changed_at, pt.id
)
SELECT * FROM info_posicao
UNION ALL
SELECT 'EVENTOS:', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
UNION ALL
SELECT * FROM eventos;
```

### Contatos

**Equipe Responsável:**
- Desenvolvimento: [equipe_dev@empresa.com]
- Infraestrutura: [infra@empresa.com]
- Negócio (SLA): [rh@empresa.com]

**Em Caso de Emergência:**
1. Executar procedimentos da seção 6
2. Documentar no ticket
3. Notificar equipe via Slack #sla-alerts

---

## 📝 Histórico de Alterações

| Data | Versão | Alteração |
|------|--------|-----------|
| 2026-03-04 | 1.0 | Versão inicial do guia (migrations 071-076) |
| 2026-03-04 | 1.1 | Adição de Migration 077 (pausas em andamento) |

---

**Fim do Guia de Manutenção e Monitoramento de SLAs**

Para dúvidas ou sugestões de melhoria, abrir issue no repositório ou contatar a equipe de desenvolvimento.
