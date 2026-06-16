# Relatório de Investigação: Divergência de Talentos

**Data:** 2026-03-19
**Analista:** Claude Code
**Status:** 🔴 PROBLEMA CRÍTICO IDENTIFICADO

---

## 📊 Resumo Executivo

### Problema Identificado

Existe uma divergência significativa entre o número de talentos armazenados no banco de dados local e o total disponível na API Inhire:

| Fonte | Quantidade | Observações |
|-------|------------|-------------|
| **Página Inhire** | 85.562 talentos | Interface web oficial |
| **Banco de Dados Local** | 61.869 talentos | Informado pelo usuário |
| **DIVERGÊNCIA** | **-23.693 talentos** | **-27,7% faltando** |

### Criticidade

🔴 **ALTA** - Mais de 1/4 dos talentos não estão sendo sincronizados, o que compromete:
- Análises de performance de recrutamento
- Relatórios para clientes
- Métricas de funil de candidaturas
- Integridade de dados históricos

---

## 🔍 Análise Técnica

### 1. Código de Sincronização Analisado

#### Arquivo: `services/api_client.py` (linhas 213-238)

```python
def get_all_talentos(self, limit: int = None, filter_dict: Dict = None):
    """
    Itera sobre todos os talentos

    NOTA: A API do InHire mudou e não aceita mais os parametros limit,
    orderBy e filter. Esses parâmetros são mantidos apenas para
    compatibilidade com código existente, mas são ignorados.
    """
    start_key = None

    while True:
        data = {}
        if start_key:
            data["exclusiveStartKey"] = start_key

        response = self._request("POST", InhireEndpoints.TALENTS_PAGINATED, data=data)
        resp = TalentosPaginatedResponse(**response)

        for talento in resp.items:
            yield talento

        if not resp.startKey:
            break
        start_key = resp.startKey
```

**✅ DIAGNÓSTICO:** O código de sincronização está CORRETO e paginando todos os talentos.

#### Arquivo: `services/sync_service.py` (linha 1357-1363)

```python
def _sync_talentos_incremental(self, filter_dict: Dict) -> Dict:
    """Sincroniza apenas talentos modificados (refatorado)"""
    return self._sync_entity_generic(
        entity_name="talentos",
        api_fetcher=self.api_client.get_all_talentos(filter_dict=filter_dict),
        db_upsert_func=self.db.upsert_talento
    )
```

**⚠️ PONTO DE ATENÇÃO:** A sincronização incremental usa `filter_dict`, que pode estar filtrando talentos!

---

### 2. Possíveis Causas da Divergência

#### 🔴 **Causa #1: Filtros na Sincronização Incremental (MAIS PROVÁVEL)**

**Problema:**
A sincronização incremental usa `filter_dict` que provavelmente filtra por `updated_at` ou `created_at`, fazendo com que:
- Talentos antigos não modificados sejam ignorados
- Novos talentos sejam sincronizados
- Mas talentos existentes e não modificados nunca sejam buscados

**Evidência:**
```python
# services/sync_service.py - linha 1361
api_fetcher=self.api_client.get_all_talentos(filter_dict=filter_dict)
```

**⚠️ NOTA IMPORTANTE:** De acordo com o código (linha 217-219), a API **não aceita mais filtros**, então mesmo que `filter_dict` seja passado, ele é **IGNORADO**. Isso significa que a causa #1 provavelmente **NÃO** é o problema!

#### 🔴 **Causa #2: Sincronização Completa Nunca Executada**

**Problema:**
Se a primeira sincronização foi feita em modo incremental, apenas talentos recentes foram buscados, e os 23.693 talentos antigos nunca entraram no banco.

**Solução:**
```bash
# Executar sincronização COMPLETA (full)
python run_sync.py --full
```

#### 🟡 **Causa #3: Erros Durante Sincronização**

**Problema:**
Erros de API, timeout, ou validação podem ter causado perda de dados durante sincronizações anteriores.

**Como Verificar:**
```sql
-- Ver logs de sincronização de TALENTOS
SELECT
    sync_entity,
    status,
    start_time,
    records_processed,
    records_created,
    records_updated,
    records_failed
FROM sync_log
WHERE sync_entity = 'TALENTOS'
ORDER BY start_time DESC
LIMIT 10;
```

#### 🟡 **Causa #4: Talentos Deletados na API mas Não no BD**

**Problema:**
O sistema pode não estar sincronizando deleções (soft delete ou hard delete) da API.

**Como Verificar:**
```sql
-- Verificar se há talentos no BD que não existem mais na API
SELECT COUNT(*)
FROM talentos
WHERE deleted_at IS NULL;  -- Se existir esta coluna
```

#### 🟡 **Causa #5: Performance do Banco de Dados**

**Problema Observado:**
Durante a investigação, consultas simples ao PostgreSQL demoraram mais de 2 minutos sem completar. Isso pode indicar:
- Falta de índices adequados
- Bloqueios (locks) de outras transações
- Tabela fragmentada (precisa de VACUUM)

**Como Resolver:**
```sql
-- 1. Verificar índices
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'talentos';

-- 2. Executar VACUUM
VACUUM ANALYZE talentos;

-- 3. Criar índice se não existir
CREATE INDEX IF NOT EXISTS idx_talentos_updated_at_inhire
ON talentos(updated_at_inhire);
```

---

### 3. Estratégia de Sincronização Atual (De Acordo com CLAUDE.md)

Segundo a documentação do projeto (`CLAUDE.md`), a estratégia recomendada é:

| Tipo de Sync | Frequência | Duração | Cobertura |
|--------------|------------|---------|-----------|
| **Sync Completa (Full)** | 1x/semana | 55 min | 100% |
| **Incremental Completa** | 1-2x/dia | 40-50 min | 100% |
| **Express** | ❌ Descontinuado | N/A | ~85% |

**⚠️ ATUALIZAÇÃO CRÍTICA (2026-03-02):**
> A otimização de "status finais" foi removida para garantir 100% de consistência.
> Sync incremental agora leva 40-50 minutos mas garante que NENHUM dado seja perdido.

**IMPORTANTE:** De acordo com a documentação, desde 03/02/2026:
- ✅ Sync incremental garante **100% de cobertura**
- ✅ Nenhum filtro por status ou data final
- ✅ Todos os talentos devem ser sincronizados

Isso torna ainda mais preocupante a divergência de 23.693 talentos!

---

## 🎯 Recomendações Imediatas

### 1. **EXECUTAR SINCRONIZAÇÃO COMPLETA (PRIORITÁRIO)**

```bash
cd "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

# Backup antes de executar
python scripts/backup/backup_database.py  # Se existir

# Executar sync FULL
python run_sync.py --full
```

**Tempo estimado:** 55 minutos
**Cobertura:** 100% dos talentos

### 2. **VERIFICAR PERFORMANCE DO BANCO**

```sql
-- Conectar ao PostgreSQL
psql -U postgres -d inhire

-- Verificar estatísticas da tabela
SELECT
    schemaname,
    relname,
    n_live_tup as "linhas vivas",
    n_dead_tup as "linhas mortas",
    last_vacuum,
    last_autovacuum,
    last_analyze
FROM pg_stat_user_tables
WHERE relname = 'talentos';

-- Se n_dead_tup > 10% de n_live_tup, executar:
VACUUM ANALYZE talentos;
```

### 3. **CRIAR ÍNDICES NECESSÁRIOS**

```sql
-- Índice para sincronização incremental
CREATE INDEX IF NOT EXISTS idx_talentos_updated_at_inhire
ON talentos(updated_at_inhire);

-- Índice para consultas por inhire_id
CREATE INDEX IF NOT EXISTS idx_talentos_inhire_id
ON talentos(inhire_id);

-- Verificar se índices foram criados
\di+ idx_talentos_*
```

### 4. **MONITORAR PRÓXIMAS SINCRONIZAÇÕES**

```sql
-- Após cada sincronização, verificar:
SELECT
    COUNT(*) as total_bd,
    MAX(updated_at_inhire) as ultima_atualizacao
FROM talentos;

-- Comparar com API (via script Python ou interface Inhire)
```

### 5. **INVESTIGAR LOGS DE ERRO**

```bash
# Ver últimas 100 linhas dos logs
tail -100 logs/inhire_sync.log

# Filtrar erros de talentos
grep -i "talento" logs/inhire_sync.log | grep -i "error\|failed"

# Ver estatísticas de sincronização
psql -U postgres -d inhire -c "
    SELECT
        sync_type,
        sync_entity,
        status,
        start_time,
        records_processed,
        records_created,
        records_updated,
        records_failed
    FROM sync_log
    WHERE sync_entity = 'TALENTOS'
    ORDER BY start_time DESC
    LIMIT 5;
"
```

---

## 📋 Checklist de Verificação

Use este checklist para resolver o problema:

- [ ] **Executar VACUUM ANALYZE na tabela talentos**
- [ ] **Criar índices recomendados**
- [ ] **Executar sincronização COMPLETA (full)**
- [ ] **Verificar logs de sincronização para erros**
- [ ] **Confirmar que os 85.562 talentos estão no BD**
- [ ] **Agendar sync full 1x/semana (domingos 02:00)**
- [ ] **Agendar sync incremental 1-2x/dia (08:00, 20:00)**
- [ ] **Configurar alertas para divergências >5%**

---

## 🔬 Investigação Adicional Necessária

### Scripts Criados para Diagnóstico

1. **`scripts/debug/investigar_divergencia_talentos.py`**
   - Conta talentos no BD
   - Conta talentos via API (paginando todos)
   - Compara e identifica divergência
   - Analisa logs de sincronização

   **Uso:**
   ```bash
   python scripts/debug/investigar_divergencia_talentos.py
   ```

   **Duração:** 5-10 minutos (API pode demorar)

### Queries SQL para Análise

```sql
-- 1. Verificar distribuição de talentos por data de criação
SELECT
    DATE_TRUNC('month', created_at) as mes,
    COUNT(*) as total_talentos
FROM talentos
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY mes DESC;

-- 2. Verificar talentos sem updated_at_inhire (nunca sincronizados?)
SELECT COUNT(*)
FROM talentos
WHERE updated_at_inhire IS NULL;

-- 3. Verificar últimas sincronizações de todas as entidades
SELECT
    sync_entity,
    MAX(start_time) as ultima_sincronizacao,
    SUM(records_processed) as total_processado,
    SUM(records_created) as total_criado,
    SUM(records_failed) as total_falhas
FROM sync_log
WHERE start_time > NOW() - INTERVAL '7 days'
GROUP BY sync_entity
ORDER BY ultima_sincronizacao DESC;
```

---

## 🚨 Alertas e Monitoramento

### Configurar Alerta de Divergência

Criar script `scripts/monitoring/check_talent_count.py`:

```python
"""
Verifica se a contagem de talentos está sincronizada
Alerta se divergência > 5%
"""
from services.api_client import InhireAPIClient
from models.database import Talento
from db.session import get_session

def check_divergence():
    # Contar no BD
    session = get_session()
    count_bd = session.query(Talento).count()

    # Contar na API (rápido via estimate)
    api_client = InhireAPIClient()
    count_api = sum(1 for _ in api_client.get_all_talentos())

    # Calcular divergência
    diff = abs(count_api - count_bd)
    pct = (diff / count_api) * 100

    if pct > 5:
        print(f"⚠️ ALERTA: Divergência de {pct:.2f}% ({diff} talentos)")
        print(f"   BD: {count_bd:,} | API: {count_api:,}")
        return False
    else:
        print(f"✅ Sincronização OK (divergência: {pct:.2f}%)")
        return True

if __name__ == "__main__":
    check_divergence()
```

### Agendar Verificação Diária

```bash
# Cron (Linux/Mac)
0 22 * * * cd /path/to/inhire && python scripts/monitoring/check_talent_count.py

# Task Scheduler (Windows)
# Criar tarefa agendada para executar diariamente às 22:00
```

---

## 📊 Próximos Passos

### Curto Prazo (Hoje)
1. ✅ Executar VACUUM ANALYZE
2. ✅ Criar índices recomendados
3. ✅ Executar sync FULL (55 min)
4. ✅ Verificar se os 85.562 talentos foram sincronizados

### Médio Prazo (Esta Semana)
1. Configurar monitoramento automático de divergência
2. Revisar logs de sincronização dos últimos 30 dias
3. Implementar alertas por e-mail/Slack
4. Documentar causa raiz do problema

### Longo Prazo (Este Mês)
1. Implementar testes automatizados de cobertura
2. Criar dashboard de monitoramento (Grafana/Metabase)
3. Otimizar performance de consultas ao BD
4. Revisar estratégia de backup e recuperação

---

## 📝 Conclusão

A divergência de **23.693 talentos (27,7%)** é um problema crítico que requer ação imediata. Com base na análise do código:

1. **O código de sincronização está CORRETO** - não há filtros sendo aplicados
2. **A API não suporta filtros** - então todos os talentos deveriam ser buscados
3. **A documentação indica 100% de cobertura** - desde 03/02/2026

**Hipótese mais provável:**
- A primeira sincronização foi feita de forma incompleta ou interrompida
- Sincronizações incrementais subsequentes apenas mantiveram os talentos já existentes
- Os 23.693 talentos "faltantes" nunca foram inseridos no BD

**Solução:**
- **Executar sincronização FULL imediatamente**
- Verificar logs para confirmar sucesso
- Implementar monitoramento para evitar reincidência

---

**Documentação gerada por:** Claude Code
**Data:** 2026-03-19
**Versão:** 1.0
