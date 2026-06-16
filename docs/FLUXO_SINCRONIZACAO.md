# Fluxo de Sincronização - InHire

## Arquivo Principal: `services/sync_service.py`

Este arquivo contém **TODA** a lógica de sincronização, tanto FULL quanto INCREMENTAL.

---

## 1. Sincronização FULL (`--full`)

### Comando:
```bash
python run_sync.py --full
```

### Método Principal:
```python
SyncService.sync_full()  # linha 34 do sync_service.py
```

### Ordem de Execução (OBRIGATÓRIA):

1. **Vagas** (independente)
   - Método: `_sync_vagas_full()` - linha 485
   - Busca TODAS as vagas da API
   - Não depende de outras entidades

2. **Posições** (depende de Vagas)
   - Método: `_sync_posicoes_full()` - linha 505
   - Busca todas as posições de cada vaga
   - Requer: Vagas já sincronizadas no BD

3. **Candidaturas** (depende de Vagas)
   - Método: `_sync_candidaturas_full()` - linha 530
   - Busca todas as candidaturas
   - Coleta IDs dos talentos para otimização
   - Requer: Vagas já sincronizadas no BD

4. **Talentos** (otimizado com IDs das Candidaturas)
   - Método: `_sync_talentos_full(talent_ids)` - linha 573
   - Se tem IDs: busca talentos específicos
   - Se não tem IDs: busca todos os talentos
   - Requer: Candidaturas já sincronizadas

5. **Entidades Secundárias:**
   - Requisições
   - Scorecard Interviews
   - Scorecard Jobs
   - Vaga Tags
   - Clientes
   - Custom Fields

### Características:
- ✓ Sincroniza **TODOS** os dados desde o início
- ✓ Não utiliza filtros de data
- ✓ Volume: ~104.558 registros
- ✓ Tempo estimado: ~55 minutos

---

## 2. Sincronização INCREMENTAL (`--incremental`)

### Comando:
```bash
python run_sync.py --incremental
```

### Método Principal:
```python
SyncService.sync_incremental(express_mode=False)  # linha 148 do sync_service.py
```

### Ordem de Execução:

1. **Vagas ABERTAS** (status='OPEN')
   - Método: `_sync_vagas_incremental()` - linha 853
   - Filtra: `status='OPEN'`
   - Compara: `updated_at` BD vs API
   - Atualiza apenas se API tem versão mais recente

2. **Posições ABERTAS** (status='open')
   - Método: `_sync_posicoes_incremental()` - linha 900
   - Filtra: `status='open'`
   - Compara: `updated_at` BD vs API

3. **Candidaturas ATIVAS** (status='ACTIVE')
   - Método: `_sync_candidaturas_incremental()` - linha 952
   - Filtra: `status='ACTIVE'`
   - Compara: `updated_at` BD vs API

4. **Candidatura Timeline**
   - Sincroniza timeline das candidaturas atualizadas

5. **Talentos** (otimizado)
   - Método: `_sync_talentos_incremental_optimized()` - linha 1125
   - Compara: `updated_at` BD vs API

6. **Scorecard Interviews**
   - Sincronização incremental

7. **Scorecard Jobs**
   - Sincronização incremental

8. **Vaga Tags**
   - Das vagas OPEN

9. **Requisições**
   - Incremental

10. **Clientes**
    - Incremental

11. **Custom Fields**
    - Incremental

### Características:
- ✓ Sincroniza apenas dados **NOVOS ou ATUALIZADOS**
- ✓ Utiliza filtros de status (OPEN, ACTIVE)
- ✓ Compara datas `updated_at` para otimização
- ✓ Tempo estimado: ~20 minutos
- ✓ Se nunca rodou antes: executa `sync_full()` automaticamente

### Estratégia de Otimização:
```python
# Exemplo: Vagas
1. Busca vagas da API com filtro: status='OPEN'
2. Para cada vaga da API:
   - Busca vaga correspondente no BD
   - Compara updated_at_api com updated_at_bd
   - Se updated_at_api > updated_at_bd: ATUALIZA
   - Se updated_at_api <= updated_at_bd: IGNORA (skipped)
   - Se não existe no BD: CRIA
```

---

## Resumo Visual

```
run_sync.py (arquivo inicial)
    │
    ├─> --full
    │   └─> sync_service.py::sync_full()
    │       ├─> _sync_vagas_full()           (TODOS)
    │       ├─> _sync_posicoes_full()        (TODOS)
    │       ├─> _sync_candidaturas_full()    (TODOS)
    │       ├─> _sync_talentos_full()        (TODOS)
    │       └─> [outras entidades...]
    │
    └─> --incremental
        └─> sync_service.py::sync_incremental(express_mode=False)
            ├─> _sync_vagas_incremental()           (OPEN + data)
            ├─> _sync_posicoes_incremental()        (open + data)
            ├─> _sync_candidaturas_incremental()    (ACTIVE + data)
            ├─> _sync_candidaturas_timeline()       (das ACTIVE)
            ├─> _sync_talentos_incremental_optimized() (data)
            └─> [outras entidades incrementais...]
```

---

## Dependências entre Entidades

```
Vagas (independente)
 ├─> Posições (precisa de Vagas)
 ├─> Candidaturas (precisa de Vagas)
 │    ├─> Talentos (otimizado com IDs de Candidaturas)
 │    └─> Timeline (precisa de Candidaturas)
 ├─> Requisições (precisa de Vagas)
 ├─> Scorecard Jobs (precisa de Vagas)
 └─> Vaga Tags (precisa de Vagas)

Scorecard Interviews (independente)
Clientes (independente)
Custom Fields (independente)
```

---

## Quando usar cada tipo?

### Use `--full` quando:
- ✓ Primeira sincronização (banco vazio)
- ✓ Reconstruir base completa
- ✓ Após mudanças estruturais no banco
- ✓ Detectar inconsistências

### Use `--incremental` quando:
- ✓ Sincronização diária/regular
- ✓ Atualizar dados recentes
- ✓ Manter dados em dia
- ✓ Economizar tempo (~20 min vs ~55 min)

---

## Arquivo Único

**Resposta direta à sua pergunta:**

Existe **UM ÚNICO ARQUIVO** que contém ambas as sincronizações:
- **Arquivo:** `services/sync_service.py`
- **Método Full:** `SyncService.sync_full()` (linha 34)
- **Método Incremental:** `SyncService.sync_incremental()` (linha 148)

O arquivo `run_sync.py` é apenas um **wrapper** que:
1. Lê os argumentos da linha de comando
2. Conecta ao banco
3. Instancia `SyncService`
4. Chama `sync_full()` ou `sync_incremental()` conforme o argumento
