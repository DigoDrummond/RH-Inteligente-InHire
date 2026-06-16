# Estratégia: Comparação com Campos Específicos de Data

## Conceito

Durante a sincronização (métodos `upsert_*`), em vez de comparar apenas o campo genérico `updated_at_inhire` do banco com `updatedAt` da API, vamos **comparar os campos específicos** de cada tabela.

## Mapeamento de Campos

### Tabela: `vagas`
- **Campo BD:** `updated_at_inhire`
- **Campo API:** `updatedAt`
- **Lógica:** Se `API.updatedAt <= BD.updated_at_inhire` → **SKIP**

### Tabela: `posicoes`
- **Campos BD:** `updated_at_inhire`, `hired_at`, `opened_at`, `approved_at`
- **Campos API:** `updatedAt`, `hiredAt`, `openedAt`, `approvedAt`
- **Lógica:** Comparar `updatedAt` primeiro. Se igual, comparar campos específicos.

### Tabela: `candidaturas`
- **Campo BD:** `updated_at_inhire`
- **Campo API:** `updatedAt`
- **Lógica Adicional:** Verificar também se `stage_name` ou `phase_name` mudaram

### Tabela: `talentos`
- **Campo BD:** `updated_at_inhire`
- **Campo API:** `updatedAt`
- **Lógica:** Se `API.updatedAt <= BD.updated_at_inhire` → **SKIP**

### Tabela: `position_timeline`
- **Campo BD:** `changed_at`
- **Campo API:** `changedAt`
- **Lógica:** Eventos são únicos por `(posicao_id, changed_at, new_status)`

### Tabela: `candidatura_timeline`
- **Campo BD:** `stage_updated_at`
- **Campo API:** Dados do stage
- **Lógica:** Comparar `stage_updated_at` com data do evento

### Tabela: `requisicoes`
- **Campo BD:** `status_updated_at`
- **Campo API:** Data de mudança de status (se disponível)
- **Lógica:** Se `status_updated_at` não mudou → **SKIP**

### Tabela: `clientes`
- **Campo BD:** `updated_at_inhire`
- **Campo API:** `updatedAt`
- **Lógica:** Se `API.updatedAt <= BD.updated_at_inhire` → **SKIP**

### Tabela: `vaga_tags`
- **Campo BD:** `updated_at` (campo interno, gerado pelo SQLAlchemy)
- **Lógica:** Tags são recriadas a cada sync (delete + insert)

## Implementação Melhorada

### Antes (Lógica Atual)

```python
def upsert_posicao(self, posicao_api, commit=True):
    existing = session.query(Posicao).filter_by(inhire_id=posicao_api.id).first()

    if existing:
        # Compara apenas updated_at_inhire
        if posicao_api.updatedAt <= existing.updated_at_inhire:
            return False, 'skipped'

        # Atualiza TODOS os campos
        existing.status = posicao_api.status
        existing.hired_at = posicao_api.hiredAt
        # ...
```

### Depois (Lógica Melhorada)

```python
def upsert_posicao(self, posicao_api, commit=True):
    existing = session.query(Posicao).filter_by(inhire_id=posicao_api.id).first()

    if existing:
        # COMPARAÇÃO COM CAMPOS ESPECÍFICOS

        # 1. Comparar updated_at_inhire (principal)
        if posicao_api.updatedAt <= existing.updated_at_inhire:
            return False, 'skipped'

        # 2. Comparar campos específicos (mesmo se updated_at for igual)
        api_hired_at = normalize_datetime(posicao_api.hiredAt)
        api_opened_at = normalize_datetime(posicao_api.openedAt)
        api_approved_at = normalize_datetime(posicao_api.approvedAt)

        # Se nenhum campo mudou, skip
        if (api_hired_at == existing.hired_at and
            api_opened_at == existing.opened_at and
            api_approved_at == existing.approved_at and
            posicao_api.status == existing.status):
            return False, 'skipped'

        # Atualizar campos
        existing.status = posicao_api.status
        existing.hired_at = api_hired_at
        existing.opened_at = api_opened_at
        existing.approved_at = api_approved_at
        # ...
```

## Benefícios

### 1. Detecção Mais Precisa de Mudanças

**Cenário:** Posição mudou de status mas `updatedAt` não foi atualizado

```
BD:
  status: 'open'
  updated_at_inhire: '2026-02-10 10:00:00'

API:
  status: 'filled'
  updatedAt: '2026-02-10 10:00:00'  # Mesma data!

Lógica Atual: SKIP (perde a mudança de status)
Lógica Melhorada: UPDATE (detecta mudança de status)
```

### 2. Campos Críticos Sempre Atualizados

Campos como `hired_at`, `status_updated_at`, `stage_updated_at` são críticos para análises e devem ser sempre verificados.

### 3. Reduz Falsos Positivos

Se apenas um campo secundário mudou (ex: descrição de vaga), mas campos críticos (status, datas) são iguais, podemos skip.

## Implementação por Tabela

### 1. Position Timeline

```python
def upsert_position_timeline(self, event_api, ...):
    # Eventos são únicos por (posicao_id, changed_at, new_status)
    existing = session.query(PositionTimeline).filter_by(
        posicao_id=posicao_db_id,
        changed_at=normalize_datetime(event_api.changedAt),
        new_status=event_api.newStatus
    ).first()

    if existing:
        # Evento já existe - comparar metadados
        if (existing.changed_by == event_api.changedBy and
            existing.reason == event_api.reason and
            existing.notes == event_api.notes):
            return False, 'skipped'

        # Atualizar metadados
        existing.changed_by = event_api.changedBy
        existing.reason = event_api.reason
        existing.notes = event_api.notes
        return False, 'updated'

    # Criar novo evento
    # ...
```

### 2. Candidaturas

```python
def upsert_candidatura(self, cand_api, job_id, commit=True):
    existing = session.query(Candidatura).filter_by(inhire_id=cand_api.id).first()

    if existing:
        # Comparar updated_at_inhire
        api_updated_at = normalize_datetime(cand_api.updatedAt)
        if api_updated_at <= existing.updated_at_inhire:
            return False, 'skipped'

        # ADICIONAL: Comparar stage/phase (campos críticos)
        api_stage_id = cand_api.stage.id if cand_api.stage else None
        api_phase_id = cand_api.phase.id if cand_api.phase else None

        # Se stage/phase não mudaram, verificar outros campos
        if (api_stage_id == existing.stage_id and
            api_phase_id == existing.phase_id and
            cand_api.status == existing.status):
            # Campos críticos iguais - considerar skip
            return False, 'skipped'

        # Atualizar
        existing.stage_id = api_stage_id
        existing.phase_id = api_phase_id
        existing.status = cand_api.status
        existing.updated_at_inhire = api_updated_at
        # ...
```

### 3. Requisições

```python
def upsert_requisicao(self, req_api, commit=True):
    existing = session.query(Requisicao).filter_by(inhire_id=req_api.id).first()

    if existing:
        # Comparar updated_at_inhire
        api_updated_at = normalize_datetime(req_api.updatedAt)
        if api_updated_at <= existing.updated_at_inhire:
            return False, 'skipped'

        # CAMPO ESPECÍFICO: status_updated_at
        api_status_updated = normalize_datetime(req_api.statusUpdatedAt)

        # Se status_updated_at não mudou, skip
        if (api_status_updated and
            existing.status_updated_at and
            api_status_updated <= existing.status_updated_at):
            return False, 'skipped'

        # Atualizar
        existing.status = req_api.status
        existing.status_updated_at = api_status_updated
        existing.updated_at_inhire = api_updated_at
        # ...
```

## Campos Críticos por Tabela

Campos que **sempre** devem ser comparados antes de skip:

### Vagas
- `status` (open/closed/paused/canceled)
- `updated_at_inhire`

### Posições
- `status`
- `hired_at`
- `approved_at`
- `opened_at`
- `updated_at_inhire`

### Candidaturas
- `status`
- `stage_id`, `stage_name`
- `phase_id`, `phase_name`
- `updated_at_inhire`

### Position Timeline
- `changed_at`
- `new_status`
- `previous_status`

### Requisições
- `status`
- `status_updated_at`
- `approved_at`
- `rejected_at`

## Fluxo de Decisão

```
1. COMPARAR updated_at_inhire (campo principal)
   ├─ API.updatedAt < BD.updated_at_inhire → SKIP
   └─ API.updatedAt >= BD.updated_at_inhire → Continuar

2. COMPARAR campos específicos críticos
   ├─ Todos iguais → SKIP
   └─ Algum diferente → UPDATE

3. ATUALIZAR apenas campos que mudaram (otimização)
```

## Exemplo Completo: upsert_posicao Melhorado

```python
def upsert_posicao(self, posicao_api: PosicaoAPI, commit=True) -> tuple[bool, str]:
    """
    Insere ou atualiza posição
    Compara campos específicos: hired_at, approved_at, opened_at, status
    """
    try:
        vaga_id = self.get_vaga_id_cached(posicao_api.jobId)
        if not vaga_id:
            return False, 'skipped'

        existing = self.session.query(Posicao).filter_by(
            inhire_id=posicao_api.id
        ).first()

        if existing:
            # ETAPA 1: Comparar updated_at_inhire (principal)
            api_updated_at = self._normalize_datetime(posicao_api.updatedAt)

            if api_updated_at and existing.updated_at_inhire:
                if api_updated_at < existing.updated_at_inhire:
                    return False, 'skipped'

            # ETAPA 2: Comparar campos específicos CRÍTICOS
            api_hired_at = self._normalize_datetime(posicao_api.hiredAt)
            api_opened_at = self._normalize_datetime(posicao_api.openedAt)
            api_approved_at = self._normalize_datetime(posicao_api.approvedAt)
            api_status = posicao_api.status

            # Se TODOS os campos críticos são iguais, SKIP
            if (api_hired_at == existing.hired_at and
                api_opened_at == existing.opened_at and
                api_approved_at == existing.approved_at and
                api_status == existing.status and
                api_updated_at == existing.updated_at_inhire):
                return False, 'skipped'

            # ETAPA 3: Atualizar (pelo menos um campo mudou)
            existing.status = api_status
            existing.hired_at = api_hired_at
            existing.opened_at = api_opened_at
            existing.approved_at = api_approved_at
            existing.updated_at_inhire = api_updated_at

            # Outros campos (menos críticos)
            existing.requisition_id = posicao_api.requisitionId
            existing.reason = posicao_api.reason
            existing.talent_id = posicao_api.talentId
            existing.time_in_current_stage = posicao_api.timeInCurrentStage
            existing.user_id = posicao_api.userId
            existing.user_name = posicao_api.userName

            if commit:
                self.session.commit()
            return False, 'updated'

        # Criar nova posição
        nova_posicao = Posicao(...)
        self.session.add(nova_posicao)
        if commit:
            self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        raise
```

## Próximos Passos

1. ✅ Identificar todos os campos críticos de cada tabela
2. ⏭️ Atualizar métodos `upsert_*` com comparação de campos específicos
3. ⏭️ Testar com dados reais
4. ⏭️ Medir impacto na performance (redução de updates desnecessários)

## Impacto Esperado

- ✅ **Detecção mais precisa** de mudanças reais
- ✅ **Redução de updates desnecessários** (menos writes no BD)
- ✅ **Dados críticos sempre atualizados** (status, datas importantes)
- ✅ **Melhor auditoria** (sabemos exatamente o que mudou)
