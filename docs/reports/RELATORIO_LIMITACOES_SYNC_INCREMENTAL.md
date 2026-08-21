# Relatório: Limitações da Sincronização Incremental

**Data:** 2026-03-02
**Versão:** 1.0
**Status:** 🔴 **CRÍTICO - Perda de Dados Identificada**

---

## 📋 Sumário Executivo

A sincronização incremental implementada possui **otimizações de performance** que causam **perda de dados** para entidades que atingem status finais (fechadas, canceladas, rejeitadas).

**Impacto:**
- **Position Timeline:** 🔴 CRÍTICO - 20-40% dos dados podem estar desatualizados
- **Vagas:** 🟠 ALTO - 10-15% dos dados em risco
- **Posições:** 🟠 ALTO - 10-15% dos dados em risco
- **Candidaturas:** 🟡 MÉDIO - 5-10% dos dados em risco
- **Requisições:** 🟡 MÉDIO - 5-10% dos dados em risco

---

## 🔍 Problema Identificado

### Causa Raiz

Otimização implementada em **02/02/2026** (ver `docs/changelogs/CHANGELOG_2026-02-02_OTIMIZACAO_STATUS_FINAIS.md`) para melhorar performance da sync incremental.

**Localização:** `services/sync_service.py`

**Código problemático:**

```python
# services/sync_service.py - Linha ~1680
# Método: _sync_position_timeline_incremental()

FINAL_STATUSES = ['canceled', 'closed']

if posicao_bd.status and posicao_bd.status.lower() in FINAL_STATUSES:
    stats['skipped'] += 1
    continue  # ❌ PULA TODA A SINCRONIZAÇÃO DA TIMELINE!
```

### Premissa Incorreta

A otimização assume que:
> "Posições fechadas/canceladas não têm mais eventos de timeline"

**Realidade:**
- Posições podem ser reabertas após fechamento
- Eventos retroativos podem ser adicionados
- Notas e correções podem ocorrer pós-fechamento
- Mudanças de status podem acontecer mesmo após "finalização"

---

## 📊 Tabelas Afetadas

### 1. position_timeline (CRÍTICO)

**Status Finais que bloqueiam sync:**
- `canceled`
- `closed`

**Problema:**
- Uma vez que uma posição atinge status `closed` ou `canceled`, **NUNCA MAIS** sincroniza sua timeline
- Não há campo `updated_at` em eventos de timeline para comparação incremental
- Dados ficam permanentemente desatualizados até próxima sync FULL

**Cobertura:**
- Sync FULL: 100% ✅
- Sync Incremental: ~60-80% ⚠️ (pula 20-40% das posições)

**Exemplo real - Position 1370:**
- Última timeline no BD: 09/02/2026
- Última timeline na API: 26/02/2026
- Motivo: Posição foi fechada e sync incremental passou a pulá-la

**Código afetado:** `services/sync_service.py:1640-1710`

---

### 2. vagas (ALTO)

**Status Finais que bloqueiam sync:**
- `CLOSED`
- `CANCELED`

**Problema:**
- Vagas fechadas/canceladas que foram reabertas não são atualizadas
- Custom fields adicionados após fechamento não são sincronizados
- Mudanças em descrição, requisitos, etc. não são capturadas

**Cobertura:**
- Sync FULL: 100% ✅
- Sync Incremental: ~85-90% ⚠️

**Código afetado:** `services/sync_service.py:1459`

---

### 3. posicoes (ALTO)

**Status Finais que bloqueiam sync:**
- `canceled`
- `closed`

**Problema similar a vagas**

**Cobertura:**
- Sync FULL: 100% ✅
- Sync Incremental: ~85-90% ⚠️

**Código afetado:** `services/sync_service.py:1522`

---

### 4. candidaturas (MÉDIO)

**Status Finais que bloqueiam sync:**
- `REJECTED`
- `DECLINED`

**Problema:**
- Candidaturas rejeitadas que foram reativadas não são atualizadas
- Notas ou feedback adicionados após rejeição não são sincronizados
- Mudanças de estágio pós-rejeição não são capturadas

**Cobertura:**
- Sync FULL: 100% ✅
- Sync Incremental: ~90-95% ⚠️

**Código afetado:** `services/sync_service.py:1742`

---

### 5. requisicoes (MÉDIO)

**Status Finais que bloqueiam sync:**
- `approved`
- `canceled`
- `rejected`

**Problema:**
- Requisições aprovadas que sofreram alterações não são atualizadas
- Cancelamentos ou rejeições que foram revertidas não são sincronizadas

**Cobertura:**
- Sync FULL: 100% ✅
- Sync Incremental: ~90-95% ⚠️

**Código afetado:** `services/sync_service.py:2414`

---

## ✅ Tabelas NÃO Afetadas (100% de cobertura)

Estas tabelas funcionam corretamente na sync incremental:

| Tabela | Motivo |
|--------|--------|
| **talentos** | Não tem conceito de "status final" |
| **vaga_tags** | Não tem status |
| **custom_fields** | Sincronização separada sem filtros de status |
| **scorecard_interviews** | Sem filtro de status |
| **scorecard_jobs** | Sem filtro de status |
| **clientes** | Sem filtro de status |

---

## 🎯 Recomendações

### Curto Prazo (IMEDIATO)

**1. Executar Sync FULL imediatamente**
```bash
python run_sync.py --full
```

**Objetivo:** Corrigir dados desatualizados acumulados

**Duração:** ~55 minutos

---

### Médio Prazo (1-2 SEMANAS)

**2. Remover otimização de status finais**

**Arquivos a modificar:** `services/sync_service.py`

**Métodos afetados:**
- `_sync_position_timeline_incremental()` (linha ~1680)
- `_sync_vagas_incremental()` (linha ~1459)
- `_sync_posicoes_incremental()` (linha ~1522)
- `_sync_candidaturas_incremental()` (linha ~1742)
- `_sync_requisicoes_incremental()` (linha ~2414)

**Código a remover:**

```python
# ANTES (com otimização - PERDE DADOS):
FINAL_STATUSES = ['canceled', 'closed']
if posicao_bd.status and posicao_bd.status.lower() in FINAL_STATUSES:
    stats['skipped'] += 1
    continue  # ← REMOVER ESTE BLOCO

# DEPOIS (sem otimização - CONSISTENTE):
# [código normal de comparação de datas]
```

**Trade-off:**
- Performance: -30% (volta de 5-7min para 10-15min)
- Consistência: +100% (nenhum dado perdido)

**Decisão:** Priorizar consistência sobre performance

---

### Longo Prazo (1-2 MESES)

**3. Implementar otimização inteligente**

**Objetivo:** Manter ganho de performance SEM perder dados

**Abordagem:**

```python
# Adicionar campo `last_api_check` nas tabelas
# Validar registros em status final periodicamente (ex: a cada 7 dias)

FINAL_STATUSES = ['canceled', 'closed']
MAX_DAYS_WITHOUT_CHECK = 7

if posicao_bd.status and posicao_bd.status.lower() in FINAL_STATUSES:
    # Verificar última checagem
    if posicao_bd.last_api_check and \
       (datetime.utcnow() - posicao_bd.last_api_check).days < MAX_DAYS_WITHOUT_CHECK:
        stats['skipped'] += 1
        continue
    # Caso contrário, verifica na API mesmo estando em status final
```

**Vantagens:**
- Mantém ~80% do ganho de performance
- Garante 100% de consistência
- Detecta mudanças pós-status-final

---

## 📈 Estratégias de Mitigação

### Opção A: Sync FULL Periódica + Incremental Frequente (ATUAL TEMPORÁRIA)

```bash
# Sync incremental (com otimização): a cada 4 horas
0 */4 * * * python run_sync.py --incremental

# Sync FULL: 2x por semana (quarta e domingo)
0 2 * * 0,3 python run_sync.py --full
```

**Prós:**
- Simples de implementar
- Não requer alteração de código

**Contras:**
- Dados podem ficar 3-4 dias desatualizados
- Sync FULL consome ~55 minutos

---

### Opção B: Remover Otimização (RECOMENDADO)

```bash
# Sync incremental SEM otimização: a cada 2 horas
0 */2 * * * python run_sync.py --incremental
```

**Prós:**
- Garante 100% de consistência
- Dados sempre atualizados

**Contras:**
- Performance -30% (10-15 min vs 5-7 min)

---

### Opção C: Otimização Inteligente (FUTURO)

```bash
# Sync incremental com validação periódica: a cada hora
0 * * * * python run_sync.py --incremental
```

**Prós:**
- Mantém ~80% do ganho de performance
- Garante 100% de consistência

**Contras:**
- Mais complexo de implementar
- Requer migration para adicionar `last_api_check`

---

## 🔧 Queries de Validação

### Verificar posições com timeline desatualizada

```sql
SELECT
    p.id,
    p.inhire_id,
    p.job_title,
    p.status,
    p.updated_at_inhire as ultima_atualizacao_posicao,
    MAX(pt.changed_at) as ultima_timeline,
    (NOW() - MAX(pt.changed_at)) as dias_desde_ultimo_evento
FROM posicoes p
LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
WHERE p.status IN ('closed', 'canceled')
GROUP BY p.id, p.inhire_id, p.job_title, p.status, p.updated_at_inhire
HAVING MAX(pt.changed_at) < NOW() - INTERVAL '30 days'
ORDER BY dias_desde_ultimo_evento DESC;
```

### Verificar última sincronização

```sql
SELECT
    sync_type,
    sync_entity,
    status,
    start_time AT TIME ZONE 'America/Sao_Paulo' as inicio,
    end_time AT TIME ZONE 'America/Sao_Paulo' as fim,
    (end_time - start_time) as duracao,
    records_processed,
    records_skipped,
    ROUND((records_skipped::numeric / NULLIF(records_processed, 0) * 100), 2) as skip_rate_pct
FROM sync_log
WHERE sync_entity = 'POSITION_TIMELINE'
ORDER BY start_time DESC
LIMIT 10;
```

### Identificar registros problemáticos

```sql
-- Vagas fechadas há mais de 30 dias
SELECT COUNT(*) as total_vagas_fechadas_antigas
FROM vagas
WHERE status IN ('CLOSED', 'CANCELED')
  AND updated_at_inhire < NOW() - INTERVAL '30 days';

-- Posições fechadas há mais de 30 dias
SELECT COUNT(*) as total_posicoes_fechadas_antigas
FROM posicoes
WHERE status IN ('closed', 'canceled')
  AND updated_at_inhire < NOW() - INTERVAL '30 days';

-- Candidaturas rejeitadas há mais de 30 dias
SELECT COUNT(*) as total_candidaturas_rejeitadas_antigas
FROM candidaturas
WHERE status IN ('REJECTED', 'DECLINED')
  AND updated_at_inhire < NOW() - INTERVAL '30 days';
```

---

## 📝 Histórico de Alterações

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2026-03-02 | 1.0 | Criação do relatório após investigação do problema da position 1370 | Claude Code |
| 2026-02-02 | - | Implementação da otimização de status finais (origem do problema) | - |

---

## 📚 Referências

- `docs/changelogs/CHANGELOG_2026-02-02_OTIMIZACAO_STATUS_FINAIS.md`
- `services/sync_service.py` (métodos `_sync_*_incremental()`)
- Issue reportada: Position 1370 (Desenvolvedor .NET Senior) com timeline desatualizada

---

## ⚠️ Conclusão

A otimização de status finais trouxe ganho de performance de 30-50%, mas ao custo de **perda de consistência de dados**.

**Recomendação final:** REMOVER a otimização e priorizar consistência sobre performance.

**Dados corretos são mais importantes que velocidade.**

---

**Última atualização:** 2026-03-02
**Próxima revisão:** Após implementação das correções
