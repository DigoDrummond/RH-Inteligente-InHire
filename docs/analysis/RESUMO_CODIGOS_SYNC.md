# Resumo: Códigos de Sincronização

## Comandos Rápidos

```bash
# SINCRONIZAÇÃO COMPLETA (primeira vez ou mensal)
python sync_completa.py

# SINCRONIZAÇÃO INCREMENTAL (diária/horária)
python sync_incremental.py
```

---

## Comparação Lado a Lado

<table>
<tr>
<th width="50%">SINCRONIZAÇÃO COMPLETA</th>
<th width="50%">SINCRONIZAÇÃO INCREMENTAL</th>
</tr>

<tr>
<td valign="top">

**Arquivo:** `sync_completa.py`

**Método Core:**
```python
sync_service.sync_full()
```

**Código:** `services/sync_service.py:32-100`

**O que faz:**
- Busca TODAS as vagas da API
- Busca TODAS as posições
- Busca TODAS as candidaturas
- Busca talentos (IDs coletados)

**Entidades:**
1. ✅ Vagas (todas)
2. ✅ Posições (todas)
3. ✅ Candidaturas (todas)
4. ✅ Talentos (IDs coletados)

**Volume:** ~104.558 registros

**Tempo:** ~55 minutos

**Filtro API:** Não usa

**Comparação:**
```python
if data_API > data_BD:
    atualizar()
else:
    skip()
```

**Atualiza:** `last_full_sync`

**Quando usar:**
- Primeira vez
- Mensalmente
- Garantir consistência total

</td>
<td valign="top">

**Arquivo:** `sync_incremental.py`

**Método Core:**
```python
sync_service.sync_incremental()
```

**Código:** `services/sync_service.py:102-145`

**O que faz:**
- Busca última sync
- Se nunca sincronizou → executa full
- Busca vagas modificadas
- Busca talentos modificados

**Entidades:**
1. ✅ Vagas (compara datas)
2. ❌ Posições (não sincroniza)
3. ❌ Candidaturas (não sincroniza)
4. ✅ Talentos (apenas modificados)

**Volume:** Variável (15-500 registros típico)

**Tempo:** ~2-5 minutos

**Filtro API:** `updatedAt >= last_sync`

**Comparação:**
```python
if data_API > data_BD:
    atualizar()
else:
    skip()
```

**Atualiza:** `last_incremental_sync`

**Quando usar:**
- Diariamente
- A cada hora
- Manter atualizado

</td>
</tr>
</table>

---

## Código Fonte Simplificado

### SINCRONIZAÇÃO COMPLETA

```python
def sync_full(self) -> Dict:
    """Sincroniza TODOS os dados"""

    # Estatísticas
    stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

    # 1. VAGAS (todas da API)
    for vaga in self.api_client.get_all_vagas():
        is_new, operation = self.db.upsert_vaga(vaga)
        stats[operation] += 1

    # 2. POSIÇÕES (todas, de cada vaga no BD)
    for vaga in self.session.query(Vaga).all():
        for posicao in self.api_client.get_all_posicoes(vaga.inhire_id):
            is_new, operation = self.db.upsert_posicao(posicao)
            stats[operation] += 1

    # 3. CANDIDATURAS (todas, de cada vaga no BD)
    talent_ids = set()
    for vaga in self.session.query(Vaga).all():
        for cand in self.api_client.get_all_candidaturas(vaga.inhire_id):
            is_new, operation = self.db.upsert_candidatura(cand, vaga.inhire_id)
            stats[operation] += 1
            talent_ids.add(cand.talentId)

    # 4. TALENTOS (apenas IDs coletados)
    for talent_id in talent_ids:
        talento = self.api_client.get_talento_by_id(talent_id)
        is_new, operation = self.db.upsert_talento(talento)
        stats[operation] += 1

    # Atualizar timestamp
    config.last_full_sync = datetime.utcnow()
    self.session.commit()

    return {'success': True, 'stats': stats}
```

---

### SINCRONIZAÇÃO INCREMENTAL

```python
def sync_incremental(self) -> Dict:
    """Sincroniza apenas modificados"""

    # Buscar última sync
    last_sync = config.last_incremental_sync or config.last_full_sync

    # Se nunca sincronizou, executar full
    if not last_sync:
        return self.sync_full()

    # Estatísticas
    stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

    # 1. VAGAS (API não suporta filtro, busca todas e compara)
    for vaga in self.api_client.get_all_vagas():
        is_new, operation = self.db.upsert_vaga(vaga)
        # upsert_vaga compara: data_API > data_BD
        stats[operation] += 1

    # 2. TALENTOS (tenta filtrar por updatedAt >= last_sync)
    filter_date = {"updatedAt": {"gte": last_sync.isoformat()}}

    for talento in self.api_client.get_all_talentos(filter_dict=filter_date):
        is_new, operation = self.db.upsert_talento(talento)
        # upsert_talento compara: data_API > data_BD
        stats[operation] += 1

    # Atualizar timestamp
    config.last_incremental_sync = datetime.utcnow()
    self.session.commit()

    return {'success': True, 'stats': stats}
```

---

## Lógica de Comparação (UPSERT)

**Ambas usam a mesma lógica:**

```python
def upsert_vaga(self, vaga_api: VagaAPI) -> tuple[bool, str]:
    """
    Insere ou atualiza vaga

    Returns: (is_new, operation)
             (True, 'created') ou (False, 'updated') ou (False, 'skipped')
    """
    existing = self.session.query(Vaga).filter_by(inhire_id=vaga_api.id).first()

    if existing:
        # REGISTRO JÁ EXISTE - COMPARAR DATAS

        if vaga_api.updatedAt and existing.updated_at_inhire:
            updated_at_normalized = self._normalize_datetime(vaga_api.updatedAt)

            # COMPARAÇÃO PRINCIPAL
            if updated_at_normalized <= existing.updated_at_inhire:
                return False, 'skipped'  # ❌ NÃO ATUALIZA (já está atual)

        # Se chegou aqui: data_API > data_BD
        # ATUALIZAR REGISTRO
        existing.name = vaga_api.name
        existing.description = vaga_api.description
        # ... outros campos
        existing.updated_at_inhire = updated_at_normalized
        existing.updated_at = datetime.utcnow()

        self.session.commit()
        return False, 'updated'  # ✅ ATUALIZADO

    else:
        # REGISTRO NÃO EXISTE - CRIAR NOVO

        nova_vaga = Vaga(
            inhire_id=vaga_api.id,
            name=vaga_api.name,
            description=vaga_api.description,
            # ... outros campos
            created_at_inhire=self._normalize_datetime(vaga_api.createdAt),
            updated_at_inhire=self._normalize_datetime(vaga_api.updatedAt)
        )

        self.session.add(nova_vaga)
        self.session.commit()
        return True, 'created'  # ✅ CRIADO
```

**Resumo:**
```
┌─────────────────────────────────────────────────────────────┐
│ FLUXO UPSERT (usado por ambas as sincronizações)           │
└─────────────────────────────────────────────────────────────┘

Registro existe no BD?
    │
    ├─ NÃO → CRIAR novo registro (INSERT)
    │         return (True, 'created')
    │
    └─ SIM → Comparar datas:
             │
             ├─ data_API <= data_BD → SKIP (não atualiza)
             │                        return (False, 'skipped')
             │
             └─ data_API > data_BD  → ATUALIZAR registro (UPDATE)
                                      return (False, 'updated')
```

---

## Arquivos do Projeto

```
G:\Meu Drive\Framework_Data\Inhire/
│
├── sync_completa.py                    # Script standalone COMPLETA
├── sync_incremental.py                 # Script standalone INCREMENTAL
├── run_sync.py                         # Script genérico (ambos)
├── scheduler.py                        # Agendador automático
│
├── services/
│   ├── sync_service.py                # Contém sync_full() e sync_incremental()
│   ├── api_client.py                  # Cliente HTTP API Inhire
│   └── database_service.py            # Lógica UPSERT (comparação de datas)
│
├── models/
│   ├── database.py                    # Modelos SQLAlchemy
│   └── api_schemas.py                 # Schemas Pydantic
│
└── docs/
    ├── COMPARACAO_SYNC_COMPLETA_VS_INCREMENTAL.md  # Comparação detalhada
    ├── LOGICA_SINCRONIZACAO_INCREMENTAL.md         # Lógica de datas
    └── RESUMO_CODIGOS_SYNC.md                      # Este arquivo
```

---

## Verificar Status do Banco

```bash
# Última sincronização
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "
SELECT
    last_full_sync AT TIME ZONE 'America/Sao_Paulo' as ultima_completa,
    last_incremental_sync AT TIME ZONE 'America/Sao_Paulo' as ultima_incremental
FROM sync_configuration;
"

# Contagem de registros
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "
SELECT
    (SELECT COUNT(*) FROM vagas) as vagas,
    (SELECT COUNT(*) FROM posicoes) as posicoes,
    (SELECT COUNT(*) FROM candidaturas) as candidaturas,
    (SELECT COUNT(*) FROM talentos) as talentos;
"
```

---

## Estratégia Recomendada

### 1️⃣ Primeira Execução

```bash
python sync_completa.py
# Aguardar ~55 minutos
# Resultado: ~104.558 registros sincronizados
```

### 2️⃣ Rotina Diária/Horária

```bash
# Manualmente
python sync_incremental.py

# OU automaticamente
python scheduler.py  # Roda incremental a cada 60 min
```

### 3️⃣ Manutenção Mensal

```bash
python sync_completa.py  # 1x por mês para garantir consistência
```

---

## Resumo Final

| Aspecto | Completa | Incremental |
|---------|----------|-------------|
| **Comando** | `python sync_completa.py` | `python sync_incremental.py` |
| **Método** | `sync_service.sync_full()` | `sync_service.sync_incremental()` |
| **Código** | `sync_service.py:32-100` | `sync_service.py:102-145` |
| **Vagas** | ✅ Todas | ✅ Compara datas |
| **Posições** | ✅ Todas | ❌ Não |
| **Candidaturas** | ✅ Todas | ❌ Não |
| **Talentos** | ✅ IDs coletados | ✅ Modificados |
| **Volume** | ~104.558 | ~15-500 |
| **Tempo** | ~55 min | ~2-5 min |
| **Comparação** | `data_API > data_BD` | `data_API > data_BD` |
| **Frequência** | Mensal | Diária/Horária |
