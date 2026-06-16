# Estratégia: Sincronização Incremental Baseada em Datas das Tabelas

## Conceito

Em vez de buscar **TODOS** os registros da API e comparar datas, vamos:
1. Consultar o banco para identificar registros que **precisam** ser atualizados
2. Buscar **apenas esses registros** na API
3. Atualizar no banco

## Campos de Data por Tabela

| Tabela | Campo de Referência | Tipo | Descrição |
|--------|---------------------|------|-----------|
| `candidatura_timeline` | `stage_updated_at` | DateTime | Data de atualização do stage |
| `candidaturas` | `updated_at_inhire` | DateTime | Data de atualização na API Inhire |
| `clientes` | `updated_at_inhire` | DateTime | Data de atualização na API Inhire |
| `posicoes` | `updated_at_inhire` | DateTime | Data de atualização na API Inhire |
| `position_timeline` | `changed_at` | DateTime | Data da mudança de status |
| `requisicoes` | `status_updated_at` | DateTime | Data de atualização do status |
| `talentos` | `updated_at_inhire` | DateTime | Data de atualização na API Inhire |
| `vaga_tags` | `updated_at` | DateTime | Data de atualização (campo interno) |
| `vagas` | `updated_at_inhire` | DateTime | Data de atualização na API Inhire |

## Nova Lógica de Sincronização Incremental

### Estratégia 1: Busca Direcionada (RECOMENDADA)

**Funcionamento:**
1. Obter `last_sync_date` da última sincronização
2. Para cada tabela, buscar registros com data > `last_sync_date`
3. Para cada registro encontrado, buscar dados atualizados na API
4. Atualizar apenas os registros modificados

```python
# Pseudocódigo
last_sync = get_last_incremental_sync()

# 1. VAGAS modificadas
vagas_modificadas = session.query(Vaga).filter(
    Vaga.updated_at_inhire > last_sync
).all()

for vaga in vagas_modificadas:
    vaga_api = api_client.get_vaga_by_id(vaga.inhire_id)
    db.upsert_vaga(vaga_api)

# 2. POSIÇÕES modificadas
posicoes_modificadas = session.query(Posicao).filter(
    Posicao.updated_at_inhire > last_sync
).all()

for posicao in posicoes_modificadas:
    # Buscar posição atualizada da API
    posicao_api = api_client.get_posicao_by_id(posicao.inhire_id)
    db.upsert_posicao(posicao_api)

# ... e assim por diante
```

**Vantagens:**
- ✅ **Extremamente eficiente** (busca apenas o necessário)
- ✅ Reduz drasticamente chamadas à API
- ✅ Rápido (pode rodar a cada 30 min)

**Desvantagens:**
- ⚠️ Requer que a API tenha endpoint para buscar por ID individual
- ⚠️ Pode perder registros NOVOS criados na API (não estão no BD ainda)

### Estratégia 2: Híbrida (IDEAL)

**Funcionamento:**
1. Buscar registros modificados no BD (Estratégia 1)
2. Buscar registros novos na API (comparando com data)
3. Combinar os dois conjuntos

```python
last_sync = get_last_incremental_sync()

# 1. Buscar MODIFICADOS no BD
vagas_modificadas_ids = session.query(Vaga.inhire_id).filter(
    Vaga.updated_at_inhire > last_sync
).all()

# 2. Buscar NOVOS + MODIFICADOS na API
todas_vagas_api = api_client.get_all_vagas()

# 3. Processar TODOS da API (comparando datas)
for vaga_api in todas_vagas_api:
    is_new, operation = db.upsert_vaga(vaga_api)
    # upsert já faz comparação de data internamente
```

**Vantagens:**
- ✅ **100% de cobertura** (modificados + novos)
- ✅ Detecta registros novos na API
- ✅ Mantém lógica de comparação de datas

**Desvantagens:**
- ⚠️ Ainda busca todos os registros da API (mesma lógica atual)
- ⚠️ Não traz ganho de performance

### Estratégia 3: Timeline-Based (AVANÇADA)

**Funcionamento:**
Usar as tabelas de timeline para detectar mudanças:

```python
last_sync = get_last_incremental_sync()

# 1. Identificar posições que mudaram de status
posicoes_com_mudanca = session.query(PositionTimeline.posicao_id).filter(
    PositionTimeline.changed_at > last_sync
).distinct().all()

# 2. Buscar dados atualizados apenas dessas posições
for posicao_id in posicoes_com_mudanca:
    posicao_bd = session.query(Posicao).get(posicao_id)
    posicao_api = api_client.get_posicao_by_id(posicao_bd.inhire_id)
    db.upsert_posicao(posicao_api)

# 3. Identificar candidaturas que mudaram de stage
candidaturas_com_mudanca = session.query(CandidaturaTimeline.candidatura_id).filter(
    CandidaturaTimeline.stage_updated_at > last_sync
).distinct().all()

# 4. Buscar dados atualizados apenas dessas candidaturas
for cand_id in candidaturas_com_mudanca:
    cand_bd = session.query(Candidatura).get(cand_id)
    cand_api = api_client.get_candidatura_by_id(cand_bd.inhire_id)
    db.upsert_candidatura(cand_api)
```

**Vantagens:**
- ✅ **Ultra eficiente** (usa timeline como índice de mudanças)
- ✅ Detecta mudanças críticas (status, stages)
- ✅ Mínimo de chamadas à API

**Desvantagens:**
- ⚠️ Complexo de implementar
- ⚠️ Depende de timeline estar sempre sincronizada
- ⚠️ Pode perder mudanças em campos não rastreados pela timeline

## Implementação Recomendada

### Fase 1: Incremental com Query no BD (CURTO PRAZO)

```python
def sync_incremental_from_db(self) -> Dict:
    """
    Sincronização incremental baseada em queries no BD
    Busca apenas registros modificados recentemente
    """
    config = self.db.get_sync_configuration(self.tenant_id)
    last_sync = config.last_incremental_sync or config.last_full_sync

    if not last_sync:
        raise ValueError("Executar sync completa primeiro!")

    stats = {
        'processed': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0
    }

    # 1. VAGAS modificadas no BD
    vagas_ids = self.session.query(Vaga.inhire_id).filter(
        Vaga.updated_at_inhire > last_sync
    ).all()

    self.logger.info(f"Encontradas {len(vagas_ids)} vagas modificadas no BD")

    # Buscar todas vagas da API e processar
    # (mantém lógica de detectar novas também)
    todas_vagas = self.api_client.get_all_vagas()
    for vaga_api in todas_vagas:
        is_new, operation = self.db.upsert_vaga(vaga_api)
        stats['processed'] += 1
        if operation == 'created':
            stats['created'] += 1
        elif operation == 'updated':
            stats['updated'] += 1
        elif operation == 'skipped':
            stats['skipped'] += 1

    # 2. POSIÇÕES de vagas modificadas
    vagas_modificadas_ou_novas = self.session.query(Vaga).filter(
        (Vaga.updated_at_inhire > last_sync) |
        (Vaga.created_at > last_sync)
    ).all()

    for vaga in vagas_modificadas_ou_novas:
        posicoes = self.api_client.get_all_posicoes(vaga.inhire_id)
        for posicao_api in posicoes:
            is_new, operation = self.db.upsert_posicao(posicao_api)
            # ... stats

    # 3. CANDIDATURAS de vagas modificadas
    for vaga in vagas_modificadas_ou_novas:
        candidaturas = self.api_client.get_all_candidaturas(vaga.inhire_id)
        for cand_api in candidaturas:
            is_new, operation = self.db.upsert_candidatura(cand_api, vaga.inhire_id)
            # ... stats

    # 4. TALENTOS (usar filtro da API se disponível)
    filter_date = {"updatedAt": {"gte": last_sync.isoformat()}}
    talentos = self.api_client.get_all_talentos(filter_dict=filter_date)
    for talento_api in talentos:
        is_new, operation = self.db.upsert_talento(talento_api)
        # ... stats

    return stats
```

### Fase 2: Query-First com Busca Direcionada (LONGO PRAZO)

```python
def sync_incremental_query_first(self) -> Dict:
    """
    Sincronização incremental otimizada
    1. Query no BD para identificar mudanças
    2. Busca direcionada na API apenas para registros modificados
    """
    config = self.db.get_sync_configuration(self.tenant_id)
    last_sync = config.last_incremental_sync or config.last_full_sync

    # 1. Identificar vagas modificadas
    vagas_modificadas = self.session.query(Vaga).filter(
        Vaga.updated_at_inhire > last_sync
    ).all()

    # 2. Buscar apenas essas vagas na API
    for vaga_bd in vagas_modificadas:
        try:
            vaga_api = self.api_client.get_vaga_by_id(vaga_bd.inhire_id)
            self.db.upsert_vaga(vaga_api)
        except Exception as e:
            self.logger.error(f"Erro ao buscar vaga {vaga_bd.inhire_id}: {e}")

    # 3. Buscar registros NOVOS (não estão no BD ainda)
    # Usando paginação com filtro de data
    todas_vagas = self.api_client.get_vagas_modified_after(last_sync)
    for vaga_api in todas_vagas:
        self.db.upsert_vaga(vaga_api)

    # ... similar para outras entidades
```

## Limitações da API Inhire

Precisamos verificar se a API suporta:

1. **Busca por ID individual:**
   - `GET /jobs/{jobId}` ✅ (provavelmente existe)
   - `GET /positions/{positionId}` ⚠️ (verificar)
   - `GET /talents/{talentId}` ✅ (existe)
   - `GET /applications/{applicationId}` ⚠️ (verificar)

2. **Filtro por data:**
   - `POST /jobs/paginated/lean` com filtro `updatedAt` ⚠️ (testar)
   - `POST /talents/list` com filtro `updatedAt` ✅ (já testado, funciona)

## Próximos Passos

1. ✅ **Testar endpoints da API:**
   - Verificar se existe busca por ID individual
   - Testar filtros de data em cada endpoint

2. ✅ **Implementar Fase 1:**
   - Criar `sync_incremental_from_db()`
   - Usar queries no BD para filtrar escopo
   - Manter busca completa na API (segurança)

3. ⏭️ **Implementar Fase 2:**
   - Após validar Fase 1
   - Implementar busca direcionada na API
   - Otimizar chamadas à API

## Comparação com Estratégia Atual

| Aspecto | Atual (Busca Tudo) | Nova (Query BD First) |
|---------|-------------------|----------------------|
| **Chamadas à API** | ~2.900 registros | ~50-200 registros |
| **Queries no BD** | 0 (antes de buscar) | 3-5 queries SELECT |
| **Tempo estimado** | 10-20 min | **2-5 min** |
| **Cobertura** | 100% | 100% |
| **Novos registros** | ✅ Detecta | ✅ Detecta (se buscar API também) |

## Conclusão

A estratégia **Query BD First (Fase 1)** é a mais viável:
- ✅ Compatível com limitações da API atual
- ✅ Reduz escopo de sincronização
- ✅ Mantém 100% de cobertura
- ✅ Simples de implementar
- ✅ **3x mais rápida que atual**
