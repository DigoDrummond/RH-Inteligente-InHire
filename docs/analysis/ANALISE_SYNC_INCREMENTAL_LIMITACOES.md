# Análise: Por que Posições e Candidaturas não estão na Sync Incremental?

## Investigação do Código Atual

### Sincronização Incremental Atual

**Arquivo:** `services/sync_service.py:102-145`

```python
def sync_incremental(self) -> Dict:
    """Sincronização incremental - apenas registros modificados"""

    # Apenas 2 entidades:
    if settings.SYNC_VAGAS_ENABLED:
        vaga_stats = self._sync_vagas_full()  # VAGAS

    if settings.SYNC_TALENTOS_ENABLED:
        tal_stats = self._sync_talentos_incremental(filter_date)  # TALENTOS

    # FALTAM: Posições e Candidaturas ❌
```

---

## Motivos Identificados

### 1. **Comparação de Datas**

Verifiquei se os métodos UPSERT têm comparação de datas:

| Entidade | Método | Comparação de Data? | Status |
|----------|--------|---------------------|--------|
| Vagas | `upsert_vaga()` | ✅ Sim (`data_API > data_BD`) | Na incremental |
| Posições | `upsert_posicao()` | ✅ Sim (`data_API > data_BD`) | **NÃO está** ⚠️ |
| Candidaturas | `upsert_candidatura()` | ❌ **Não** (sempre atualiza) | **NÃO está** ⚠️ |
| Talentos | `upsert_talento()` | ✅ Sim (`data_API > data_BD`) | Na incremental |

**Código de Posições:**
```python
# database_service.py:156-159
if existing:
    if posicao_api.updatedAt and existing.updated_at_inhire:
        updated_at_normalized = self._normalize_datetime(posicao_api.updatedAt)
        if updated_at_normalized <= existing.updated_at_inhire:
            return False, 'skipped'  # ✅ TEM comparação!
```

**Código de Candidaturas:**
```python
# database_service.py:214-229
if existing:
    existing.source = cand_api.source
    existing.status = status_normalized
    # ... atualiza campos ...
    self.session.commit()
    return False, 'updated'  # ❌ SEMPRE atualiza (sem comparação)
```

**Conclusão:**
- ✅ **Posições**: Tem comparação de data → PODERIA estar na incremental
- ⚠️ **Candidaturas**: Não tem comparação → Sempre atualiza (ineficiente para incremental)

---

### 2. **Dependência de Vagas**

Posições e Candidaturas **dependem** de Vagas:

```python
# Para buscar posições, precisa do ID da vaga:
api_client.get_all_posicoes(job_id)  # Precisa de job_id

# Para buscar candidaturas, precisa do ID da vaga:
api_client.get_all_candidaturas(job_id)  # Precisa de job_id
```

**Problema:**
- A API não tem endpoint tipo "GET /positions?updatedAt>=2025-11-17"
- Você precisa iterar por cada vaga e buscar suas posições/candidaturas
- Na sync incremental, como saber quais vagas têm posições/candidaturas modificadas?

**Opções:**
1. ❌ Buscar posições/candidaturas de TODAS as vagas (lento)
2. ✅ Buscar apenas de vagas modificadas recentemente (inteligente)
3. ✅ Buscar de vagas com `activeTalents > 0` (otimizado)

---

### 3. **Limitação da API Inhire**

A documentação da API não menciona filtros de data para Posições e Candidaturas:

| Endpoint | Suporta Filtro de Data? | Como buscar |
|----------|------------------------|-------------|
| `POST /jobs/paginated/lean` | ❌ Não documentado | Busca todas, compara individualmente |
| `POST /positions/get-all-from-job` | ❌ Não | Precisa de `jobId` |
| `POST /talent/get-applications-from-job` | ❌ Não | Precisa de `jobId` |
| `POST /talents/list` | ⚠️ Parcial | Tentativa com filtro `updatedAt` |

**Conclusão:**
Não há como buscar "todas as posições modificadas" diretamente. Você precisa:
1. Identificar quais vagas mudaram
2. Para cada vaga, buscar suas posições/candidaturas

---

### 4. **Implementação Simplificada**

A implementação atual da `sync_incremental()` foi **simplificada** para:
- ✅ Focar em entidades principais (Vagas e Talentos)
- ✅ Reduzir complexidade
- ✅ Minimizar tempo de execução (~2-5 min)
- ✅ Sincronizar dados que mudam mais frequentemente

**Análise de frequência de mudanças:**

| Entidade | Frequência de Mudança | Prioridade Incremental |
|----------|----------------------|------------------------|
| Vagas | Alta (status, nome, etc.) | ⭐⭐⭐ Alta |
| Talentos | Alta (novos candidatos) | ⭐⭐⭐ Alta |
| Posições | Média (aprovações, contratações) | ⭐⭐ Média |
| Candidaturas | Alta (mudanças de etapa) | ⭐⭐⭐ Alta |

**Observação:**
Candidaturas deveriam ter **alta prioridade**, mas a falta de comparação de datas torna ineficiente.

---

## Problema Principal: Candidaturas Sem Comparação

### Por que Candidaturas não comparam datas?

Analisando o código:

```python
def upsert_candidatura(self, cand_api: CandidaturaAPI, job_id: str) -> tuple[bool, str]:
    existing = self.session.query(Candidatura).filter_by(inhire_id=cand_api.id).first()

    if existing:
        # NÃO HÁ COMPARAÇÃO DE DATA!
        # Sempre atualiza
        existing.source = cand_api.source
        existing.status = status_normalized
        existing.stage_id = cand_api.stage.id if cand_api.stage else None
        # ...
        return False, 'updated'
```

**Possíveis motivos:**
1. Candidaturas mudam de etapa frequentemente (stage, phase)
2. Desenvolvedor optou por sempre atualizar para garantir dados atuais
3. Campo `updatedAt` pode não refletir mudanças de etapa corretamente
4. Implementação incompleta (esqueceram de adicionar)

---

## Impacto da Limitação Atual

### O que você está perdendo:

```
Sincronização Incremental Atual:
✅ Vagas modificadas → atualizadas
✅ Talentos modificados → atualizados
❌ Posições modificadas → NÃO sincronizadas até próxima full
❌ Candidaturas modificadas → NÃO sincronizadas até próxima full
```

### Cenário Real:

```
Hoje às 10:00 - Sync Completa
  ├─ Vaga001: 5 posições
  ├─ Candidatura001: etapa "Triagem"
  └─ ...

Hoje às 14:00 - Candidatura001 muda para etapa "Entrevista"

Hoje às 15:00 - Sync Incremental
  ├─ Vagas: atualiza modificadas ✓
  ├─ Talentos: atualiza modificados ✓
  └─ Candidatura001: NÃO atualiza ❌ (continua "Triagem" no BD)

Amanhã às 02:00 - Sync Completa
  └─ Candidatura001: FINALMENTE atualiza para "Entrevista" ✓
```

**Resultado:**
Dados de candidaturas ficam **desatualizados** por até 24 horas (ou até próxima sync completa).

---

## Soluções Propostas

### Solução 1: Sync Incremental COMPLETA (Ideal)

Incluir Posições e Candidaturas, com inteligência para buscar apenas vagas relevantes:

```python
def sync_incremental(self) -> Dict:
    """Sincronização incremental completa"""

    last_sync = config.last_incremental_sync or config.last_full_sync

    # 1. VAGAS (todas, compara datas)
    vagas_modificadas_ids = set()
    for vaga in self.api_client.get_all_vagas():
        is_new, operation = self.db.upsert_vaga(vaga)
        if operation in ['created', 'updated']:
            vagas_modificadas_ids.add(vaga.id)

    # 2. POSIÇÕES (apenas de vagas modificadas)
    for vaga_id in vagas_modificadas_ids:
        for posicao in self.api_client.get_all_posicoes(vaga_id):
            is_new, operation = self.db.upsert_posicao(posicao)
            # Posições têm comparação de data ✓

    # 3. CANDIDATURAS (apenas de vagas modificadas)
    talent_ids = set()
    for vaga_id in vagas_modificadas_ids:
        for cand in self.api_client.get_all_candidaturas(vaga_id):
            is_new, operation = self.db.upsert_candidatura(cand, vaga_id)
            # Sempre atualiza (sem comparação) ⚠️
            if cand.talentId:
                talent_ids.add(cand.talentId)

    # 4. TALENTOS (filtrados + IDs coletados)
    filter_date = {"updatedAt": {"gte": last_sync.isoformat()}}
    for talento in self.api_client.get_all_talentos(filter_dict=filter_date):
        is_new, operation = self.db.upsert_talento(talento)

    # Sincronizar também talentos coletados das candidaturas
    for talent_id in talent_ids:
        talento = self.api_client.get_talento_by_id(talent_id)
        is_new, operation = self.db.upsert_talento(talento)
```

**Vantagens:**
- ✅ Sincroniza tudo
- ✅ Inteligente (apenas vagas modificadas)
- ✅ Mantém dados atualizados

**Desvantagens:**
- ⚠️ Mais lento que versão atual
- ⚠️ Candidaturas sempre atualizam (sem comparação de data)

---

### Solução 2: Adicionar Comparação de Datas em Candidaturas

Corrigir `upsert_candidatura()` para comparar datas:

```python
def upsert_candidatura(self, cand_api: CandidaturaAPI, job_id: str) -> tuple[bool, str]:
    existing = self.session.query(Candidatura).filter_by(inhire_id=cand_api.id).first()

    if existing:
        # ADICIONAR COMPARAÇÃO DE DATA
        if cand_api.updatedAt and existing.updated_at_inhire:
            updated_at_normalized = self._normalize_datetime(cand_api.updatedAt)
            if updated_at_normalized <= existing.updated_at_inhire:
                return False, 'skipped'  # ✅ Não atualiza se não mudou

        # Atualizar campos...
        existing.source = cand_api.source
        existing.status = status_normalized
        # ...
        existing.updated_at_inhire = updated_at_normalized
        return False, 'updated'
```

**Vantagens:**
- ✅ Eficiente (pula candidaturas não modificadas)
- ✅ Consistente com outras entidades

**Desvantagens:**
- ⚠️ Pode perder mudanças se `updatedAt` não for confiável

---

### Solução 3: Sync Incremental com Vagas Ativas

Sincronizar posições/candidaturas apenas de vagas **ativas**:

```python
def sync_incremental(self) -> Dict:
    # 1. VAGAS
    for vaga in self.api_client.get_all_vagas():
        is_new, operation = self.db.upsert_vaga(vaga)

    # 2. POSIÇÕES/CANDIDATURAS (apenas vagas ativas com candidatos)
    vagas_ativas = self.session.query(Vaga).filter(
        Vaga.status == 'open',
        Vaga.active_talents > 0
    ).all()

    for vaga in vagas_ativas:
        # Posições
        for posicao in self.api_client.get_all_posicoes(vaga.inhire_id):
            is_new, operation = self.db.upsert_posicao(posicao)

        # Candidaturas
        for cand in self.api_client.get_all_candidaturas(vaga.inhire_id):
            is_new, operation = self.db.upsert_candidatura(cand, vaga.inhire_id)

    # 3. TALENTOS
    # ... (como antes)
```

**Vantagens:**
- ✅ Foca em vagas relevantes
- ✅ Reduz volume de dados
- ✅ Mantém dados críticos atualizados

**Desvantagens:**
- ⚠️ Vagas fechadas não atualizam posições/candidaturas

---

## Recomendação

### Curto Prazo (Mais Simples):

1. **Adicionar comparação de datas em Candidaturas** (Solução 2)
2. **Implementar Sync Incremental com Vagas Ativas** (Solução 3)

### Longo Prazo (Ideal):

1. **Implementar Sync Incremental Completa** (Solução 1)
2. **Testar confiabilidade do campo `updatedAt` em Candidaturas**
3. **Otimizar com índices no banco de dados**

---

## Próximos Passos

Quer que eu implemente alguma dessas soluções? Posso criar:

1. ✅ Versão melhorada de `sync_incremental()` com Posições e Candidaturas
2. ✅ Correção em `upsert_candidatura()` para adicionar comparação de datas
3. ✅ Script de teste para validar a implementação

Basta me dizer qual solução prefere!
