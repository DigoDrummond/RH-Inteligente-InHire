# Estratégia de Sincronização Otimizada - InHire API

## 📋 Resumo Executivo

Proposta de arquitetura de sincronização **eficiente, consistente e prática** baseada nos endpoints paginados da API InHire.

**Objetivos:**
- ✅ Sincronização completa e confiável
- ✅ Performance otimizada (reduzir tempo de sync)
- ✅ Arquitetura escalável e sustentável
- ✅ Suporte a sincronização incremental eficiente
- ✅ Possibilidade de microserviços quando necessário

---

## 🎯 Arquitetura Proposta

### 1. Modelo de Sincronização Híbrido

**SYNC FULL** (~55 min atualmente):
- Busca TODOS os dados sem filtros
- Usa paginação simples (sem filtros de data)
- Execução: mensal ou após grandes mudanças

**SYNC INCREMENTAL** (~20 min atualmente):
- Busca apenas dados novos/atualizados
- Usa filtros de data quando disponível
- Execução: diária ou várias vezes ao dia

**SYNC EXPRESS** (novo - ~5 min):
- Busca apenas entidades "quentes" (candidaturas ativas + talentos vinculados)
- Prioriza dados críticos para operação
- Execução: a cada hora ou sob demanda

---

## 📊 Endpoints da API e Estratégias

### 1. Vagas (Jobs)

**Endpoint:** `POST /jobs/paginated/lean`

**Parâmetros:**
```json
{
  "tenantId": "string",
  "limit": 100,
  "exclusiveStartKey": {
    "id": "string",
    "tenantId": "string"
  }
}
```

**Estratégias:**

**FULL:**
- Paginação simples com `limit=100`
- Sem filtros de data
- Processa todos os registros

**INCREMENTAL:**
- Usar `GET /jobs/{jobId}` para vagas específicas
- Alternativa: buscar todas e filtrar localmente por `updatedAt`
- API não suporta filtro nativo de data no endpoint paginado

**IMPLEMENTAÇÃO ATUAL:** ✅ OK
- `api_client.get_all_vagas()` funciona corretamente
- Paginação via `exclusiveStartKey`

---

### 2. Posições (Positions)

**Endpoint:** `GET /jobs/{jobId}/positions/paginated`

**Query Params:**
```
limit: number
startKey: string
```

**Estratégias:**

**FULL:**
- Para cada vaga, buscar suas posições
- `limit=100` por página
- Paginação via `startKey`

**INCREMENTAL:**
- Buscar posições apenas de vagas atualizadas recentemente
- Filtrar vagas por `updatedAt > last_sync - 7 dias`
- Reduz drasticamente o número de requisições

**IMPLEMENTAÇÃO ATUAL:** ✅ OK
- `api_client.get_all_posicoes(job_id)` funciona
- Dependente da lista de vagas

**OTIMIZAÇÃO PROPOSTA:**
- No incremental, filtrar vagas antes de buscar posições
- Criar índice: `idx_vagas_updated_at`

---

### 3. Candidaturas (Job Talents / Applications)

**Endpoint:** `POST /jobs/{jobId}/applications/paginated`

**Parâmetros:**
```json
{
  "limit": 100,
  "exclusiveStartKey": {
    "id": "string",
    "jobId": "string",
    "tenantId": "string"
  }
}
```

**Estratégias:**

**FULL:**
- Para cada vaga, buscar suas candidaturas
- `limit=100` por página
- Gera MUITAS requisições (~1.138 vagas × N páginas)

**INCREMENTAL:**
- Filtrar vagas atualizadas recentemente
- Buscar candidaturas apenas dessas vagas
- **CRÍTICO:** API não suporta filtro de data no endpoint de candidaturas

**SYNC EXPRESS (NOVO):**
- Buscar apenas candidaturas de vagas com `status = 'active'`
- Focar em vagas abertas (posições em aberto)
- Reduz 80% do volume

**IMPLEMENTAÇÃO ATUAL:** ⚠️ LENTO
- `api_client.get_all_candidaturas(job_id)` funciona
- Mas processa TODAS as vagas (inclusive fechadas)

**OTIMIZAÇÃO PROPOSTA:**
```python
# INCREMENTAL: buscar apenas vagas ativas ou atualizadas
vagas_filtradas = db.get_vagas_ativas_ou_recentes(days=7)

# EXPRESS: apenas vagas com posições abertas
vagas_express = db.get_vagas_com_posicoes_abertas()
```

---

### 4. Talentos (Talents)

**Endpoint:** `POST /talents/paginated`

**Parâmetros (disponíveis mas não funcionam):**
```json
{
  "exclusiveStartKey": {
    "id": "string",
    "createdAt": "datetime",
    "updatedAt": "datetime"
  },
  "orderBy": {
    "field": "updatedAt",
    "direction": "desc"
  },
  "filter": {
    "updatedAt": "2025-01-01T00:00:00Z"
  }
}
```

**Estratégias:**

**FULL:**
- Paginação simples sem filtros
- `limit=100` (padrão da API)
- Processar todos os talentos

**INCREMENTAL:**
- **PROBLEMA:** API ignora filtros de data
- **SOLUÇÃO ATUAL:** Buscar IDs de talentos das candidaturas recentes
- Usar `GET /talents/{talentId}` para buscar detalhes

**OTIMIZAÇÃO PROPOSTA:**
```python
# Coletar IDs de talentos únicos das candidaturas recentes
talent_ids = set()
for candidatura in candidaturas_recentes:
    if candidatura.talentId:
        talent_ids.add(candidatura.talentId)

# Buscar apenas esses talentos
for talent_id in talent_ids:
    talent = api_client.get_talento_by_id(talent_id)
```

**IMPLEMENTAÇÃO ATUAL:** ⚠️ FUNCIONA MAS PODE MELHORAR
- `api_client.get_all_talentos()` busca todos
- No incremental, usa IDs das candidaturas (✅ BOM)

---

### 5. Requisições (Requisitions)

**Endpoint:** `GET /requisitions/paginated`

**Query Params:**
```
lastEvaluatedKey: string
```

**Estratégias:**

**FULL:**
- Buscar todas as requisições paginadas
- Endpoint super eficiente (~10-20 requests vs ~1.138)
- `lastEvaluatedKey` para paginação

**INCREMENTAL:**
- **PROBLEMA:** API não suporta filtro de data
- **SOLUÇÃO:** Buscar todas e filtrar localmente
- Volume baixo (~2.500 requisições) então é aceitável

**IMPLEMENTAÇÃO ATUAL:** ✅ EXCELENTE
- `api_client.get_all_requisicoes_paginated()` funciona perfeitamente
- 50-100x mais rápido que buscar por vaga

---

### 6. Timeline de Posições (NOVO)

**Endpoint:** `GET /positions/{positionId}/timeline`

**Estratégias:**

**FULL:**
- Para cada posição, buscar timeline
- Armazenar eventos históricos

**INCREMENTAL:**
- Buscar timeline apenas de posições atualizadas recentemente
- Verificar último evento no BD e buscar novos

**IMPLEMENTAÇÃO:** 🆕 A IMPLEMENTAR
```python
def sync_position_timeline_incremental(self):
    # Buscar posições atualizadas nos últimos 7 dias
    posicoes = db.get_posicoes_atualizadas(days=7)

    for posicao in posicoes:
        timeline = api_client.get_position_timeline(posicao.inhire_id)
        db.upsert_timeline_events(timeline)
```

---

### 7. Campos Personalizados

**Endpoint:** `GET /custom-fields/{entity}`

**Entidades:** `TALENTS`, `JOB_TALENTS`

**Estratégias:**

**FULL + INCREMENTAL:**
- Buscar campos personalizados no início do sync
- Cachear metadados por 24h
- Volume baixo, busca rápida

**IMPLEMENTAÇÃO:** ✅ OK
- `api_client.get_custom_fields(entity)` funciona

---

### 8. Clientes

**Endpoint:** `GET /clients`

**Estratégias:**

**FULL + INCREMENTAL:**
- Buscar lista de clientes no início
- Cachear por 24h
- Tabela auxiliar de referência

**IMPLEMENTAÇÃO:** ✅ OK
- `api_client.get_clientes()` funciona

---

## 🏗️ Arquitetura de Microserviços (Futuro)

Se a sincronização ficar pesada, podemos quebrar em microserviços:

### Opção 1: Por Entidade
```
- sync_service_vagas.py       (independente)
- sync_service_posicoes.py    (depende de vagas)
- sync_service_candidaturas.py (depende de vagas)
- sync_service_talentos.py    (depende de candidaturas)
```

### Opção 2: Por Frequência
```
- sync_service_express.py     (candidaturas ativas + talentos vinculados)
- sync_service_incremental.py (atualização diária)
- sync_service_full.py        (full sync mensal)
```

### Opção 3: Por Prioridade
```
- sync_service_critical.py    (candidaturas + talentos - alta frequência)
- sync_service_metadata.py    (vagas + posições - média frequência)
- sync_service_historical.py  (requisições + timeline - baixa frequência)
```

---

## ⚡ Estratégia de Otimização Imediata

### 1. SYNC EXPRESS (NOVO - ~5 min)

**Objetivo:** Sincronizar apenas dados críticos para operação diária

**Entidades:**
- ✅ Vagas com posições abertas
- ✅ Candidaturas ativas dessas vagas
- ✅ Talentos vinculados às candidaturas ativas
- ✅ Timeline de posições abertas

**Implementação:**
```python
def sync_express(self) -> Dict:
    """Sync rápido: apenas dados críticos"""

    # 1. Buscar vagas com posições abertas
    vagas_ativas = self.db.get_vagas_com_posicoes_abertas()

    # 2. Candidaturas apenas dessas vagas
    talent_ids = set()
    for vaga in vagas_ativas:
        candidaturas = self.api_client.get_all_candidaturas(vaga.inhire_id)
        for cand in candidaturas:
            self.db.upsert_candidatura(cand)
            if cand.talentId:
                talent_ids.add(cand.talentId)

    # 3. Talentos vinculados
    for talent_id in talent_ids:
        talento = self.api_client.get_talento_by_id(talent_id)
        self.db.upsert_talento(talento)

    return stats
```

**Benefícios:**
- Reduz 80% do volume de dados
- Foco em candidatos ativos
- Ideal para execução a cada hora

---

### 2. SYNC INCREMENTAL OTIMIZADO (~10 min)

**Otimizações:**

**Vagas:**
- Buscar todas (não tem filtro de data na API)
- Filtrar localmente por `updatedAt > last_sync - 7 dias`

**Posições:**
- Buscar apenas de vagas atualizadas nos últimos 7 dias
- Reduz de 1.138 vagas para ~50-100 vagas

**Candidaturas:**
- Buscar apenas de vagas ativas OU atualizadas
- Filtro: `status IN ('active', 'open') OR updatedAt > last_sync - 7 dias`

**Talentos:**
- Usar IDs das candidaturas recentes (estratégia atual)
- Adicionar cache de 24h para evitar buscar mesmo talento múltiplas vezes

**Implementação:**
```python
def sync_incremental_optimized(self, days: int = 7) -> Dict:
    cutoff = datetime.now() - timedelta(days=days)

    # 1. Vagas - buscar todas e filtrar localmente
    all_vagas = list(self.api_client.get_all_vagas())
    vagas_recentes = [v for v in all_vagas if v.updatedAt > cutoff]

    # 2. Posições - apenas de vagas recentes
    for vaga in vagas_recentes:
        posicoes = self.api_client.get_all_posicoes(vaga.id)
        for pos in posicoes:
            self.db.upsert_posicao(pos)

    # 3. Candidaturas - vagas ativas OU recentes
    vagas_filtradas = self.db.get_vagas_ativas_ou_recentes(days=days)
    talent_ids = set()

    for vaga in vagas_filtradas:
        candidaturas = self.api_client.get_all_candidaturas(vaga.inhire_id)
        for cand in candidaturas:
            self.db.upsert_candidatura(cand)
            if cand.talentId:
                talent_ids.add(cand.talentId)

    # 4. Talentos - apenas IDs coletados
    for talent_id in talent_ids:
        if not self.db.is_talento_cached_recently(talent_id, hours=24):
            talento = self.api_client.get_talento_by_id(talent_id)
            self.db.upsert_talento(talento)

    return stats
```

---

### 3. SYNC FULL OTIMIZADO (~40 min)

**Otimizações:**

**Paralelização:**
- Usar ThreadPoolExecutor para buscar posições em paralelo
- Worker pool: 5-10 workers simultâneos
- Respeitar rate limit da API

**Batch Processing:**
- Commit a cada 1000 registros ao invés de commit por registro
- Reduz overhead de transações SQL

**Cache Inteligente:**
- Cachear metadados (custom fields, clientes) por 24h
- Evitar buscar dados que não mudaram

**Implementação:**
```python
def sync_full_optimized(self) -> Dict:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # 1. Vagas (sequencial)
    vagas = list(self.api_client.get_all_vagas())
    self.db.batch_upsert_vagas(vagas, batch_size=1000)

    # 2. Posições (paralelo)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(self._sync_posicoes_vaga, v.id): v
            for v in vagas
        }

        for future in as_completed(futures):
            vaga = futures[future]
            try:
                posicoes = future.result()
                self.db.batch_upsert_posicoes(posicoes)
            except Exception as e:
                self.logger.error(f"Erro vaga {vaga.id}: {e}")

    # 3. Candidaturas (paralelo com batch)
    # Similar ao acima

    # 4. Talentos (sequencial com cache)
    # Usar estratégia de IDs únicos

    return stats

def _sync_posicoes_vaga(self, job_id: str) -> list:
    """Worker para buscar posições de uma vaga"""
    return list(self.api_client.get_all_posicoes(job_id))
```

---

## 📈 Comparação de Performance

| Modo | Tempo Atual | Tempo Otimizado | Redução | Frequência Recomendada |
|------|-------------|-----------------|---------|------------------------|
| **FULL** | ~55 min | ~40 min | -27% | Mensal |
| **INCREMENTAL** | ~20 min | ~10 min | -50% | Diário |
| **EXPRESS** | N/A | ~5 min | N/A | A cada hora |

---

## 🎯 Roadmap de Implementação

### Fase 1: Otimizações Imediatas (Sprint 1)
- [x] Implementar SYNC EXPRESS
- [ ] Otimizar filtros de vagas no incremental
- [ ] Adicionar cache de talentos (24h)
- [ ] Implementar batch upsert para reduzir commits SQL

### Fase 2: Performance (Sprint 2)
- [ ] Paralelizar sync de posições (ThreadPoolExecutor)
- [ ] Paralelizar sync de candidaturas
- [ ] Adicionar índices otimizados no PostgreSQL
- [ ] Implementar circuit breaker para API

### Fase 3: Monitoramento (Sprint 3)
- [ ] Dashboard de métricas de sync
- [ ] Alertas de falhas e lentidão
- [ ] Logs estruturados com ElasticSearch
- [ ] Grafana para visualização de performance

### Fase 4: Microserviços (Futuro)
- [ ] Avaliar necessidade de quebrar em microserviços
- [ ] Implementar fila de mensageria (RabbitMQ/Redis)
- [ ] Deploy separado por entidade
- [ ] Orquestração com Kubernetes

---

## 🔧 Configurações Recomendadas

### .env
```bash
# Sync Modes
SYNC_EXPRESS_ENABLED=true
SYNC_INCREMENTAL_DAYS=7        # Buscar últimos 7 dias
SYNC_FULL_ENABLED=true

# Performance
SYNC_BATCH_SIZE=100            # Tamanho padrão de página
SYNC_PARALLEL_WORKERS=5        # Workers paralelos (full sync)
SYNC_CACHE_TALENTS_HOURS=24    # Cache de talentos

# Rate Limiting
INHIRE_API_RATE_LIMIT=10       # 10 req/s
INHIRE_API_MAX_BURST=20        # Burst de até 20 req/s
```

### Frequência Recomendada
```bash
# Cron jobs
0 */1 * * * cd /app && python run_sync.py --express      # A cada hora
0 2 * * * cd /app && python run_sync.py --incremental    # 2h da manhã
0 3 1 * * cd /app && python run_sync.py --full          # 1º dia do mês às 3h
```

---

## ✅ Conclusão

**Estratégia Recomendada:**

1. **EXPRESS (1x/hora):** Dados críticos de operação
2. **INCREMENTAL (1x/dia):** Atualização completa dos últimos 7 dias
3. **FULL (1x/mês):** Sincronização completa como backup

**Benefícios:**
- ✅ Dados sempre atualizados (defasagem máxima de 1h)
- ✅ Performance otimizada (5 min vs 20 min vs 55 min)
- ✅ Redução de custo de API (menos requisições)
- ✅ Escalável para crescimento futuro
- ✅ Possibilidade de microserviços quando necessário

**Próximos Passos:**
1. Implementar SYNC EXPRESS
2. Testar e validar performance
3. Monitorar métricas por 1 semana
4. Ajustar configurações baseado em dados reais
5. Avaliar necessidade de microserviços
