# Resposta: Lógica de Sincronização Incremental

## Suas Perguntas

### 1. "A sincronização incremental ocorrerá a partir da última data que foi atualizada?"

**Resposta: SIM ✓**

A sincronização incremental usa a data da última sincronização como ponto de partida:

```python
# sync_service.py linha 112-113
config = self.db.get_sync_configuration(self.tenant_id)
last_sync = config.last_incremental_sync or config.last_full_sync
```

**Exemplo:**
```
Última sincronização: 2025-11-16 10:00:00

Na próxima sync incremental:
- Busca dados modificados APÓS 2025-11-16 10:00:00
- Compara individualmente cada registro
- Atualiza apenas se necessário
```

---

### 2. "Considerando se a data do BD for menor que a requisição, a atualização deve ser feita."

**Resposta: SIM, EXATAMENTE! ✓**

A lógica implementada é:

```
SE data_BD < data_API  →  ATUALIZA ✓
SE data_BD >= data_API →  SKIP (não atualiza)
```

---

## Demonstração Prática

Execute o exemplo para ver a lógica funcionando:

```bash
python exemplo_sync_incremental.py
```

**Saída esperada:**

```
[CENÁRIO 1] Data da API é MAIOR que data do BD
  Data no BD:  2025-11-15 14:30:00
  Data da API: 2025-11-17 09:00:00

  Comparação: 2025-11-17 09:00:00 > 2025-11-15 14:30:00?
  Resultado:  True

  [OK] ACAO: ATUALIZAR o registro no banco
```

---

## Código Implementado

### Localização: `services/database_service.py`

#### Vagas (linhas 76-79)

```python
if existing:
    if vaga_api.updatedAt and existing.updated_at_inhire:
        updated_at_normalized = self._normalize_datetime(vaga_api.updatedAt)
        if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
            return False, 'skipped'  # NÃO ATUALIZA

    # Se chegou aqui: data_API > data_BD
    existing.name = vaga_api.name
    existing.updated_at_inhire = updated_at_normalized
    return False, 'updated'  # ATUALIZA
```

#### Posições (linhas 156-159)

```python
if existing:
    if posicao_api.updatedAt and existing.updated_at_inhire:
        updated_at_normalized = self._normalize_datetime(posicao_api.updatedAt)
        if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
            return False, 'skipped'

    # Atualiza...
    return False, 'updated'
```

#### Talentos (linhas 269-272)

```python
if existing:
    if talento_api.updatedAt and existing.updated_at_inhire:
        updated_at_normalized = self._normalize_datetime(talento_api.updatedAt)
        if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
            return False, 'skipped'

    # Atualiza...
    return False, 'updated'
```

#### Candidaturas (linhas 214-229)

⚠️ **ATENÇÃO:** Candidaturas **NÃO TEM** comparação de data!

```python
if existing:
    # NÃO compara datas - sempre atualiza
    existing.status = status_normalized
    existing.stage_id = cand_api.stage.id if cand_api.stage else None
    return False, 'updated'  # SEMPRE ATUALIZA
```

---

## Fluxo Completo

```
┌─────────────────────────────────────────────────────────────┐
│ [1] BUSCAR ÚLTIMA SINCRONIZAÇÃO                             │
│     last_sync = 2025-11-16 10:00:00                         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ [2] BUSCAR DADOS DA API                                     │
│     (idealmente filtrados por updatedAt >= last_sync)       │
│                                                             │
│     API retorna:                                            │
│     - vaga001 (updatedAt: 2025-11-17 09:00)                │
│     - vaga002 (updatedAt: 2025-11-15 08:00)                │
│     - vaga003 (updatedAt: 2025-11-16 15:00) [NOVA]         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ [3] PROCESSAR CADA REGISTRO (UPSERT)                        │
└─────────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌─────────────────┐           ┌──────────────────┐
│ vaga001         │           │ vaga002          │
│ Existe no BD    │           │ Existe no BD     │
│                 │           │                  │
│ BD:  15/11 14h  │           │ BD:  16/11 12h   │
│ API: 17/11 09h  │           │ API: 15/11 08h   │
│                 │           │                  │
│ 17/11 > 15/11?  │           │ 15/11 > 16/11?   │
│ SIM → ATUALIZA  │           │ NÃO → SKIP       │
└─────────────────┘           └──────────────────┘
        ↓                               ↓
    UPDATED                         SKIPPED

        ┌───────────────────────────────┐
        ↓
┌─────────────────┐
│ vaga003         │
│ NÃO existe no BD│
│                 │
│ CRIAR NOVO      │
└─────────────────┘
        ↓
    CREATED
```

---

## Resultado

```
Processados: 3
Criados:     1 (vaga003)
Atualizados: 1 (vaga001)
Ignorados:   1 (vaga002)
```

---

## Normalização de Datas

Para garantir comparação correta, as datas são normalizadas:

```python
def _normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Remove timezone para permitir comparação com datas do BD
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)  # Remove timezone
    return dt
```

**Por quê?**
- PostgreSQL armazena datas **sem timezone** (naive)
- API retorna datas **com timezone** (aware)
- Sem normalização, a comparação falharia

---

## Comandos para Executar

### Sincronização Incremental

```bash
# Comando principal
python run_sync.py --incremental

# Ou script standalone
python sync_incremental.py
```

### Verificar Última Sincronização

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "
SELECT
    tenant_id,
    last_incremental_sync AT TIME ZONE 'America/Sao_Paulo' as ultima_incremental,
    last_full_sync AT TIME ZONE 'America/Sao_Paulo' as ultima_completa
FROM sync_configuration;
"
```

---

## Resumo Final

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Comparação de datas** | ✅ SIM | `data_API > data_BD` → atualiza |
| **Última sync como base** | ✅ SIM | Usa `last_incremental_sync` |
| **Vagas** | ✅ Compara | Atualiza se `data_API > data_BD` |
| **Posições** | ✅ Compara | Atualiza se `data_API > data_BD` |
| **Talentos** | ✅ Compara | Atualiza se `data_API > data_BD` |
| **Candidaturas** | ⚠️ Não compara | Sempre atualiza |

---

## Documentação Adicional

- **Lógica completa:** `docs/LOGICA_SINCRONIZACAO_INCREMENTAL.md`
- **Demonstração:** `exemplo_sync_incremental.py`
- **Código fonte:** `services/database_service.py`
