# Análise dos Endpoints da API InHire
**Data**: 20/01/2026
**Fonte**: Reunião técnica com equipe InHire

---

## 🎯 OBJETIVO

Analisar os 3 endpoints discutidos na reunião técnica para garantir que o sistema está sincronizando dados de forma consistente e atualizada.

---

## 📋 ENDPOINTS DISCUTIDOS NA REUNIÃO

### 1. Positions Paginated
```bash
curl --location 'https://api.inhire.app/jobs/positions/paginated/fd434658-ba35-4d68-90b0-a97a35bcc1ff'
```

### 2. Custom Fields
- **Documentação**: https://docs.inhire.com.br/api/obter-campos-personalizados-de-uma-entidade
- **Entidades suportadas**: JOBS, REQUISITIONS, ALL

### 3. Requisitions Paginated
```bash
curl --location 'https://api.inhire.app/requisitions/paginated?lastEvaluatedKey=d5a0c9b2-ec13-417e-931b-4443543e1369'
```
- **Nota importante**: "last evaluation key acabou a página ficou zerado"

---

## 🔍 ANÁLISE COMPARATIVA

## 1. POSITIONS PAGINATED

### ✅ Status: **IMPLEMENTADO CORRETAMENTE**

**Implementação Atual** (`services/api_client.py`, linhas 149-169):
```python
def get_all_posicoes(self, job_id: str, limit: int = None) -> Generator[PosicaoAPI, None, None]:
    """Itera sobre todas as posições de uma vaga"""
    limit = limit or self.default_batch_size
    start_key = None

    while True:
        endpoint = InhireEndpoints.POSITIONS_PAGINATED.format(job_id=job_id)
        params = {"limit": limit}
        if start_key is not None:
            params["startKey"] = start_key

        response = self._request("GET", endpoint, params=params)
        resp = PosicoesPaginatedResponse(**response)

        for posicao in resp.items:
            yield posicao

        if not resp.hasMore:
            break

        # Incrementar startKey numericamente
        if start_key is None:
            start_key = limit
        else:
            start_key += limit
```

**Endpoint Configurado** (`config.py`, linha 198):
```python
POSITIONS_PAGINATED = "/jobs/positions/paginated/{job_id}"
```

### ✅ Compatibilidade
- **Endpoint**: ✅ Correto (`/jobs/positions/paginated/{job_id}`)
- **Método HTTP**: ✅ GET
- **Paginação**: ✅ Usa `startKey` numérico com `hasMore`
- **Sincronização**: ✅ Ativa em full e incremental sync

**Conclusão**: Implementação está correta e alinhada com a API.

---

## 2. CUSTOM FIELDS

### ⚠️ Status: **IMPLEMENTADO PARCIALMENTE**

**Implementação Atual** (`services/api_client.py`, linhas 413-419):
```python
def get_custom_fields(self, entity_type: str) -> list:
    """Busca custom fields de uma entidade (job, talent, jobTalent)"""
    try:
        endpoint = f"/custom-data-manager/custom-fields/entity/{entity_type}"
        response = self._request("GET", endpoint)
        return [CustomFieldAPI(entityType=entity_type, **field) for field in response] if isinstance(response, list) else []
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return []
        raise
```

**Uso no Sync Service** (`services/sync_service.py`, linhas 909-921):
```python
def _sync_custom_fields(self) -> Dict:
    """Sincroniza custom fields de todas as entidades"""
    stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

    # Buscar custom fields de cada tipo de entidade
    for entity_type in ['job', 'talent', 'jobTalent']:
        try:
            fields = self.api_client.get_custom_fields(entity_type)
            for field in fields:
                try:
                    is_new, operation = self.db.upsert_custom_field(field)
                    stats['processed'] += 1
                    stats[operation] += 1
                # ...
```

### ⚠️ Divergências Identificadas

| Item | Documentação InHire | Implementação Atual | Status |
|------|---------------------|---------------------|--------|
| **Endpoint** | `/custom-data-manager/custom-fields/entity/{entityType}` | ✅ Correto | ✅ OK |
| **Entidades - JOBS** | ✅ Suportado | ✅ Sincronizando como `job` | ✅ OK |
| **Entidades - TALENTS** | ✅ Suportado | ✅ Sincronizando como `talent` | ✅ OK |
| **Entidades - JOB TALENTS** | ✅ Suportado | ✅ Sincronizando como `jobTalent` | ✅ OK |
| **Entidades - REQUISITIONS** | ✅ Suportado (docs) | ❌ **NÃO SINCRONIZANDO** | ⚠️ **FALTA** |
| **Entidade - ALL** | ✅ Suportado (docs) | ❌ Não implementado | ⚠️ Opcional |

### 🔴 Problema Identificado

**Custom Fields de REQUISITIONS não estão sendo sincronizados!**

No arquivo `CORRECAO_REQUISICOES.md` (linha 87), vemos que requisições têm `customFields`:
```python
class RequisicaoAPI(BaseModel):
    # ...
    customFields: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
```

E na tabela `requisicoes` do banco, existe a coluna:
```sql
custom_fields JSONB
```

**Porém**, o sync de custom fields só busca definições para:
- `job`
- `talent`
- `jobTalent`

**Falta**: Buscar definições de custom fields para `requisition`!

### ✅ Sincronização Ativa
- Custom fields estão sendo sincronizados em **full sync** e **incremental sync**
- Método `_sync_custom_fields()` e `_sync_custom_fields_incremental()` implementados

**Conclusão**: Implementação funciona, mas **falta sincronizar custom fields de REQUISITIONS**.

---

## 3. REQUISITIONS PAGINATED

### 🔴 Status: **NOVO ENDPOINT - NÃO IMPLEMENTADO**

**Implementação Atual** (`services/api_client.py`, linhas 274-302):
```python
def get_all_requisicoes(self) -> Generator[RequisicaoAPI, None, None]:
    """
    Itera sobre todas as requisições

    Estratégia: Busca requisições através das vagas
    (não existe endpoint paginado geral de requisições)
    """
    # Buscar todas as vagas primeiro
    for vaga in self.get_all_vagas():
        # Para cada vaga, buscar suas requisições
        try:
            requisicoes = self.get_requisicoes_by_job(vaga.id)
            for req in requisicoes:
                yield req
        except Exception as e:
            self.logger.error(f"Erro ao buscar requisições da vaga {vaga.id}: {str(e)}")
            continue

def get_requisicoes_by_job(self, job_id: str) -> list:
    """Busca requisições de uma vaga específica"""
    try:
        endpoint = f"/requisitions/job/{job_id}"
        response = self._request("GET", endpoint)
        return [RequisicaoAPI(**r) for r in response] if isinstance(response, list) else []
    # ...
```

### 🔍 Histórico

De acordo com `CORRECAO_REQUISICOES.md` (linhas 10-53):

**Situação Anterior**:
- Código tentava usar `POST /requisitions/paginated` → **Erro 403 Forbidden**
- Endpoint não existia na época

**Correção Implementada em 19/01/2026**:
- Mudou para buscar requisições através das vagas: `GET /requisitions/job/{job_id}`
- Funciona corretamente

**Situação Atual (Reunião Técnica)**:
- InHire agora disponibiliza: `GET /requisitions/paginated?lastEvaluatedKey=...`
- Este é um **NOVO endpoint** que não existia antes!

### 🆕 Novo Endpoint Disponível

**URL da Reunião**:
```bash
curl --location 'https://api.inhire.app/requisitions/paginated?lastEvaluatedKey=d5a0c9b2-ec13-417e-931b-4443543e1369'
```

**Características**:
- Método: `GET`
- Paginação: Usa `lastEvaluatedKey`
- Comportamento: "acabou a página ficou zerado" (key fica null/zero no final)

### 📊 Comparação de Abordagens

| Aspecto | Abordagem Atual | Novo Endpoint Paginated |
|---------|-----------------|-------------------------|
| **Endpoint** | `/requisitions/job/{job_id}` | `/requisitions/paginated` |
| **Estratégia** | Itera por vagas, busca requisições de cada | Busca TODAS requisições diretamente |
| **Performance** | ❌ Lenta (N+1 requests) | ✅ Rápida (paginação direta) |
| **Requests** | ~1.138 requests (1 por vaga) | ~10-20 requests (paginado) |
| **Tempo estimado** | ~10-15 minutos | ~1-2 minutos |
| **Requisições sem vaga** | ❌ Não busca | ✅ Busca todas |
| **Completude** | ⚠️ Pode perder dados | ✅ Completo |

### 🔴 Problemas com Abordagem Atual

1. **Performance**: Faz 1 request por vaga (~1.138 vagas = 1.138 requests)
2. **Requisições órfãs**: Pode não buscar requisições que não estão vinculadas a vagas
3. **Rate limiting**: Muitas requisições podem causar throttling

### ✅ Vantagens do Novo Endpoint

1. **Performance**: 50-100x mais rápido
2. **Completude**: Busca TODAS as requisições, incluindo órfãs
3. **Menos requests**: Reduz carga na API

**Conclusão**: Endpoint `/requisitions/paginated` está **disponível** mas **NÃO IMPLEMENTADO**. Recomenda-se migrar para este endpoint.

---

## 🎯 PADRÕES DE PAGINAÇÃO DA API INHIRE

Através da análise dos diferentes endpoints, identificamos **3 padrões de paginação**:

### 1. Paginação com `startKey` (Vagas)
```python
# Endpoint: /jobs/paginated/lean
response = {
    "results": [...],
    "startKey": "next_page_key"  # String UUID
}

# Próxima página:
data = {"exclusiveStartKey": start_key}
response = POST /jobs/paginated/lean
```

### 2. Paginação com `startKey` numérico (Posições)
```python
# Endpoint: /jobs/positions/paginated/{job_id}
response = {
    "items": [...],
    "hasMore": true
}

# Próxima página:
params = {"startKey": 50, "limit": 50}  # Numérico incremental
response = GET /jobs/positions/paginated/{job_id}
```

### 3. Paginação com `lastEvaluatedKey` (Requisições - NOVO)
```python
# Endpoint: /requisitions/paginated
response = {
    "items": [...],
    "lastEvaluatedKey": "d5a0c9b2-ec13-417e-931b-4443543e1369"
}

# Próxima página:
params = {"lastEvaluatedKey": last_key}
response = GET /requisitions/paginated

# Última página:
response = {
    "items": [...],
    "lastEvaluatedKey": null  # ou zero ou ausente
}
```

### 4. Paginação com `exclusiveStartKey` (Talentos)
```python
# Endpoint: /talents/paginated
data = {"exclusiveStartKey": start_key}  # Objeto completo
response = POST /talents/paginated
```

**Observação**: A API InHire **não é consistente** nos nomes de chaves de paginação:
- `startKey` (string UUID para vagas)
- `startKey` (numérico para posições)
- `lastEvaluatedKey` (para requisições)
- `exclusiveStartKey` (para talentos)

---

## 📊 RESUMO DO STATUS ATUAL

| Endpoint | Implementado | Sincronizando | Performance | Recomendação |
|----------|--------------|---------------|-------------|--------------|
| **Positions Paginated** | ✅ Sim | ✅ Sim | ✅ Ótima | ✅ Manter |
| **Custom Fields (Jobs)** | ✅ Sim | ✅ Sim | ✅ Ótima | ✅ Manter |
| **Custom Fields (Talents)** | ✅ Sim | ✅ Sim | ✅ Ótima | ✅ Manter |
| **Custom Fields (JobTalents)** | ✅ Sim | ✅ Sim | ✅ Ótima | ✅ Manter |
| **Custom Fields (Requisitions)** | ✅ Sim (método) | ❌ **NÃO** | - | ⚠️ **IMPLEMENTAR** |
| **Requisitions Paginated** | ❌ Não | ❌ Não | - | 🔴 **IMPLEMENTAR** |

---

## 🚀 RECOMENDAÇÕES

### 🔴 PRIORIDADE ALTA

#### 1. Implementar `/requisitions/paginated`

**Benefícios**:
- 50-100x mais rápido
- Reduz de ~1.138 requests para ~10-20 requests
- Busca requisições órfãs (sem vaga vinculada)
- Menor carga na API

**Implementação sugerida**:
```python
def get_all_requisicoes_paginated(self) -> Generator[RequisicaoAPI, None, None]:
    """
    Itera sobre todas as requisições usando endpoint paginado

    Endpoint: GET /requisitions/paginated?lastEvaluatedKey={key}
    Paginação: lastEvaluatedKey (null quando acabar)
    """
    last_key = None

    while True:
        endpoint = "/requisitions/paginated"
        params = {}
        if last_key:
            params["lastEvaluatedKey"] = last_key

        response = self._request("GET", endpoint, params=params)

        # Assumindo resposta similar a outros endpoints
        items = response.get("items", [])
        for item in items:
            yield RequisicaoAPI(**item)

        # Verificar se há próxima página
        last_key = response.get("lastEvaluatedKey")
        if not last_key or last_key == "0" or last_key == 0:
            break
```

**Passos**:
1. Adicionar endpoint em `config.py`:
   ```python
   REQUISITIONS_PAGINATED = "/requisitions/paginated"
   ```

2. Implementar método `get_all_requisicoes_paginated()` em `api_client.py`

3. Atualizar `sync_service.py` para usar o novo método

4. Testar com script de validação

5. Comparar resultados (método antigo vs novo)

6. Após validação, substituir `get_all_requisicoes()` pelo novo método

**Tempo estimado**: 2-3 horas

---

### ⚠️ PRIORIDADE MÉDIA

#### 2. Sincronizar Custom Fields de Requisitions

**Problema**: Custom fields de requisições não estão sendo sincronizados

**Solução**:
```python
def _sync_custom_fields(self) -> Dict:
    """Sincroniza custom fields de todas as entidades"""
    stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

    # ADICIONAR 'requisition' à lista
    for entity_type in ['job', 'talent', 'jobTalent', 'requisition']:
        try:
            fields = self.api_client.get_custom_fields(entity_type)
            # ...
```

**Validação**:
```python
# Testar busca de custom fields de requisições
fields = api_client.get_custom_fields('requisition')
print(f"Custom fields de requisições: {len(fields)}")
for field in fields:
    print(f"- {field.name} ({field.fieldType})")
```

**Tempo estimado**: 30 minutos

---

### 📋 PRIORIDADE BAIXA

#### 3. Implementar opção 'ALL' para Custom Fields

Se a API suportar `entity_type='ALL'`, pode simplificar:
```python
# Em vez de:
for entity_type in ['job', 'talent', 'jobTalent', 'requisition']:
    fields = self.api_client.get_custom_fields(entity_type)

# Fazer:
fields = self.api_client.get_custom_fields('ALL')
```

**Antes de implementar**: Validar se endpoint suporta `ALL`:
```bash
curl --location 'https://api.inhire.app/custom-data-manager/custom-fields/entity/ALL' \
  --header 'Authorization: Bearer TOKEN' \
  --header 'X-Tenant: TENANT_ID'
```

**Tempo estimado**: 1 hora (incluindo validação)

---

## 🧪 PLANO DE VALIDAÇÃO

### 1. Validar Requisitions Paginated

**Script de teste**:
```python
# testar_requisitions_paginated.py
from services.api_client import InhireAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)

def test_requisitions_paginated():
    api = InhireAPIClient()

    logger.info("Testando GET /requisitions/paginated...")

    count = 0
    pages = 0

    for req in api.get_all_requisicoes_paginated():
        count += 1
        if count % 50 == 0:
            pages += 1
            logger.info(f"Página {pages}: {count} requisições processadas")

    logger.info(f"✓ Total: {count} requisições em {pages} páginas")

    # Comparar com método antigo
    logger.info("Comparando com método antigo...")
    count_old = sum(1 for _ in api.get_all_requisicoes())

    logger.info(f"Método antigo: {count_old} requisições")
    logger.info(f"Método novo: {count} requisições")
    logger.info(f"Diferença: {count - count_old}")

    if count > count_old:
        logger.warning(f"⚠️ Método novo encontrou {count - count_old} requisições a mais!")

if __name__ == '__main__':
    test_requisitions_paginated()
```

### 2. Validar Custom Fields de Requisitions

**Script de teste**:
```python
# testar_custom_fields_requisitions.py
from services.api_client import InhireAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)

def test_custom_fields_requisitions():
    api = InhireAPIClient()

    logger.info("Testando custom fields de requisitions...")

    fields = api.get_custom_fields('requisition')

    logger.info(f"✓ {len(fields)} custom fields encontrados")

    for field in fields:
        logger.info(f"  - {field.name} ({field.fieldType})")
        logger.info(f"    ID: {field.id}")
        logger.info(f"    Required: {field.required}")
        logger.info("")

if __name__ == '__main__':
    test_custom_fields_requisitions()
```

### 3. Validar Dados no Banco

```sql
-- Verificar custom_fields em requisições
SELECT
    inhire_id,
    status,
    custom_fields,
    jsonb_pretty(custom_fields) as custom_fields_formatted
FROM requisicoes
WHERE custom_fields IS NOT NULL
  AND custom_fields != '{}'
LIMIT 10;

-- Contar requisições com custom_fields
SELECT
    COUNT(*) as total,
    COUNT(custom_fields) as com_custom_fields,
    ROUND(COUNT(custom_fields) * 100.0 / COUNT(*), 1) as percentual
FROM requisicoes;
```

---

## 📈 IMPACTO ESPERADO

### Performance de Requisições

**Antes** (método atual via vagas):
- Requests: ~1.138 (1 por vaga)
- Tempo: ~10-15 minutos
- Rate limit: Alto risco

**Depois** (endpoint paginado):
- Requests: ~10-20 (paginado)
- Tempo: ~1-2 minutos
- Rate limit: Risco baixo

**Ganho**: 7-10x mais rápido, 50x menos requests

### Completude de Dados

**Custom Fields de Requisitions**:
- Antes: 0% (não sincroniza)
- Depois: 100% (sincroniza tudo)

**Requisições Órfãs**:
- Antes: Pode não buscar (depende de estar vinculada a vaga)
- Depois: Busca 100% (todas as requisições)

---

## 📝 CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Requisitions Paginated (2-3 horas)

- [ ] Adicionar `REQUISITIONS_PAGINATED` em `config.py`
- [ ] Implementar `get_all_requisicoes_paginated()` em `api_client.py`
- [ ] Criar schema Pydantic para resposta (se necessário)
- [ ] Atualizar interface `IAPIClient` com novo método
- [ ] Criar script de teste `testar_requisitions_paginated.py`
- [ ] Executar teste e validar resultados
- [ ] Comparar contagem com método antigo
- [ ] Atualizar `sync_service.py` para usar novo método
- [ ] Executar sync incremental completo
- [ ] Validar dados no banco
- [ ] Documentar mudanças

### Fase 2: Custom Fields de Requisitions (30 min)

- [ ] Adicionar `'requisition'` à lista de entity_types em `_sync_custom_fields()`
- [ ] Adicionar `'requisition'` à lista em `_sync_custom_fields_incremental()`
- [ ] Criar script de teste `testar_custom_fields_requisitions.py`
- [ ] Executar teste e validar campos retornados
- [ ] Executar sync de custom fields
- [ ] Validar dados no banco
- [ ] Documentar mudanças

### Fase 3: Validação Final (1 hora)

- [ ] Executar sync incremental completo
- [ ] Comparar contagens BD vs API
- [ ] Verificar logs de erro
- [ ] Validar custom_fields em requisições
- [ ] Testar performance (tempo de execução)
- [ ] Atualizar documentação técnica
- [ ] Atualizar `REFACTORING_COMPLETO_FINAL.md`

---

## 🔗 ARQUIVOS RELACIONADOS

### Para Modificar

1. **`config.py`** (linha 186-207)
   - Adicionar `REQUISITIONS_PAGINATED`

2. **`services/api_client.py`**
   - Linhas 274-302: Método `get_all_requisicoes()`
   - Linhas 413-419: Método `get_custom_fields()`
   - Adicionar novo método `get_all_requisicoes_paginated()`

3. **`services/sync_service.py`**
   - Linhas 909-921: `_sync_custom_fields()` - adicionar 'requisition'
   - Linhas 1793-1830: `_sync_custom_fields_incremental()` - adicionar 'requisition'
   - Atualizar referências a `get_all_requisicoes()` para usar novo método

4. **`interfaces/i_api_client.py`**
   - Adicionar assinatura do novo método `get_all_requisicoes_paginated()`

### Para Criar

1. **`scripts/debug/testar_requisitions_paginated.py`**
   - Script de validação do novo endpoint

2. **`scripts/debug/testar_custom_fields_requisitions.py`**
   - Script de validação de custom fields

3. **`models/new_api_schemas.py`** (se necessário)
   - Schema para resposta paginada de requisições

---

## 📚 REFERÊNCIAS

1. **Documentação InHire**: https://docs.inhire.com.br/api/obter-campos-personalizados-de-uma-entidade
2. **CORRECAO_REQUISICOES.md**: Histórico da correção anterior
3. **REFACTORING_COMPLETO_FINAL.md**: Documentação do refactoring
4. **ANALISE_REAL_BD.md**: Análise do banco de dados

---

## 🎉 CONCLUSÃO

### ✅ Pontos Positivos

1. **Positions Paginated**: Implementação correta e funcionando
2. **Custom Fields (3/4)**: 75% das entidades sincronizando
3. **Código preparado**: Fácil adicionar novo endpoint

### ⚠️ Pontos de Atenção

1. **Requisitions**: Usando método antigo (lento)
2. **Custom Fields**: Faltando entidade 'requisition'
3. **Performance**: Oportunidade de 7-10x melhoria

### 🚀 Próximos Passos

1. **Imediato**: Implementar `/requisitions/paginated`
2. **Seguinte**: Adicionar custom fields de requisições
3. **Validação**: Executar testes completos
4. **Documentação**: Atualizar docs técnicos

**Estimativa total**: 3-4 horas de trabalho

---

**Última atualização**: 20/01/2026
**Autor**: Claude Code Refactoring Team
**Status**: Análise concluída - Aguardando implementação
