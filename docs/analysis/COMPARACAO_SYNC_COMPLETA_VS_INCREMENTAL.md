# Comparação: Sincronização Completa vs Incremental

## Resumo Executivo

| Aspecto | Sincronização Completa | Sincronização Incremental |
|---------|------------------------|---------------------------|
| **Arquivo** | `sync_completa.py` | `sync_incremental.py` |
| **Método** | `sync_service.sync_full()` | `sync_service.sync_incremental()` |
| **Código** | `services/sync_service.py:32-100` | `services/sync_service.py:102-145` |
| **Volume** | TODOS os dados (~104.558 registros) | Apenas modificados |
| **Tempo** | ~55 minutos | ~2-5 minutos |
| **Quando usar** | Primeira vez ou mensalmente | Diariamente/horário |
| **Filtro API** | Não usa filtro | Tenta filtrar por `updatedAt` |

---

## Código Fonte Comparado

### 1. SINCRONIZAÇÃO COMPLETA

**Localização:** `services/sync_service.py:32-100`

```python
def sync_full(self) -> Dict:
    """
    Sincronização completa - importa TODOS os dados
    """
    self.logger.info("=== INICIANDO SINCRONIZAÇÃO COMPLETA ===")

    config = self.db.get_sync_configuration(self.tenant_id)
    main_log = self.db.create_sync_log(config.id, SyncType.FULL, SyncEntity.ALL)

    all_stats = {
        'processed': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0
    }

    try:
        # 1. VAGAS (PRIMEIRO - OBRIGATÓRIO)
        if settings.SYNC_VAGAS_ENABLED:
            self.logger.info(">>> Sincronizando VAGAS...")
            vaga_stats = self._sync_vagas_full()
            self._merge_stats(all_stats, vaga_stats)

        # 2. POSIÇÕES (SEGUNDO - DEPENDE DE VAGAS)
        if settings.SYNC_POSICOES_ENABLED:
            self.logger.info(">>> Sincronizando POSIÇÕES...")
            pos_stats = self._sync_posicoes_full()
            self._merge_stats(all_stats, pos_stats)

        # 3. CANDIDATURAS (TERCEIRO - DEPENDE DE VAGAS)
        talent_ids = set()
        if settings.SYNC_CANDIDATURAS_ENABLED:
            self.logger.info(">>> Sincronizando CANDIDATURAS...")
            cand_stats, talent_ids = self._sync_candidaturas_full()
            self._merge_stats(all_stats, cand_stats)

        # 4. TALENTOS (QUARTO - OTIMIZADO COM IDs DAS CANDIDATURAS)
        if settings.SYNC_TALENTOS_ENABLED:
            self.logger.info(">>> Sincronizando TALENTOS...")
            tal_stats = self._sync_talentos_full(talent_ids)
            self._merge_stats(all_stats, tal_stats)

        # Finalizar
        config.last_full_sync = datetime.utcnow()
        self.session.commit()

        self.db.complete_sync_log(main_log, SyncStatus.SUCCESS, all_stats)

        self.logger.info("=== SINCRONIZAÇÃO COMPLETA FINALIZADA ===")
        return {
            'success': True,
            'status': SyncStatus.SUCCESS,
            'stats': all_stats
        }

    except Exception as e:
        self.logger.error(f"Erro na sincronização completa: {str(e)}", exc_info=True)
        self.db.complete_sync_log(main_log, SyncStatus.ERROR, all_stats, errors=str(e))
        return {
            'success': False,
            'status': SyncStatus.ERROR,
            'error': str(e),
            'stats': all_stats
        }
```

**Características:**
- ✅ Sincroniza **4 entidades** em ordem
- ✅ Busca **TODOS** os registros da API
- ✅ Compara `data_API > data_BD` individualmente
- ✅ Atualiza `last_full_sync` ao final
- ⏱️ Tempo: ~55 minutos

---

### 2. SINCRONIZAÇÃO INCREMENTAL

**Localização:** `services/sync_service.py:102-145`

```python
def sync_incremental(self) -> Dict:
    """
    Sincronização incremental - apenas registros modificados
    """
    self.logger.info("=== INICIANDO SINCRONIZAÇÃO INCREMENTAL ===")

    config = self.db.get_sync_configuration(self.tenant_id)
    last_sync = config.last_incremental_sync or config.last_full_sync

    # SE NUNCA SINCRONIZOU, EXECUTA FULL AUTOMATICAMENTE
    if not last_sync:
        self.logger.warning("Nenhuma sincronização anterior, executando full sync")
        return self.sync_full()

    main_log = self.db.create_sync_log(config.id, SyncType.INCREMENTAL, SyncEntity.ALL)
    all_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

    try:
        # FILTRO DE DATA (para endpoints que suportam)
        filter_date = {"updatedAt": {"gte": last_sync.isoformat()}}

        # Sincronizar apenas 2 entidades principais
        if settings.SYNC_VAGAS_ENABLED:
            # Vagas: API não suporta filtro, busca todas e compara individualmente
            vaga_stats = self._sync_vagas_full()
            self._merge_stats(all_stats, vaga_stats)

        if settings.SYNC_TALENTOS_ENABLED:
            # Talentos: tenta usar filtro de data
            tal_stats = self._sync_talentos_incremental(filter_date)
            self._merge_stats(all_stats, tal_stats)

        # Atualizar timestamp
        config.last_incremental_sync = datetime.utcnow()
        self.session.commit()

        self.db.complete_sync_log(main_log, SyncStatus.SUCCESS, all_stats)

        self.logger.info("=== SINCRONIZAÇÃO INCREMENTAL FINALIZADA ===")
        return {'success': True, 'status': SyncStatus.SUCCESS, 'stats': all_stats}

    except Exception as e:
        self.logger.error(f"Erro na sincronização incremental: {str(e)}", exc_info=True)
        self.db.complete_sync_log(main_log, SyncStatus.ERROR, all_stats, errors=str(e))
        return {'success': False, 'status': SyncStatus.ERROR, 'error': str(e)}
```

**Características:**
- ✅ Busca `last_incremental_sync` ou `last_full_sync`
- ✅ Se nunca sincronizou → executa **full** automaticamente
- ✅ Sincroniza **2 entidades** (Vagas e Talentos)
- ✅ Tenta filtrar por `updatedAt >= last_sync`
- ✅ Compara `data_API > data_BD` individualmente
- ✅ Atualiza `last_incremental_sync` ao final
- ⏱️ Tempo: ~2-5 minutos

---

## Diferenças Principais

### Entidades Sincronizadas

| Entidade | Completa | Incremental | Motivo |
|----------|----------|-------------|--------|
| Vagas | ✅ Sim | ✅ Sim | Sempre sincroniza |
| Posições | ✅ Sim | ❌ Não | Depende de Vagas (completa faz) |
| Candidaturas | ✅ Sim | ❌ Não | Depende de Vagas (completa faz) |
| Talentos | ✅ Sim | ✅ Sim | Principais mudanças |

**Por que incremental não sincroniza Posições e Candidaturas?**
- Implementação atual foca em Vagas e Talentos (entidades principais)
- Posições e Candidaturas mudam menos frequentemente
- Pode ser estendido para incluí-las se necessário

---

### Fluxo de Execução

#### COMPLETA:
```
1. Buscar TODAS as vagas da API
   ↓
2. Para cada vaga no BD:
   ├─ Buscar TODAS as posições dessa vaga
   ├─ Buscar TODAS as candidaturas dessa vaga
   └─ Coletar IDs dos talentos
   ↓
3. Buscar talentos (apenas IDs coletados)
   ↓
4. Atualizar last_full_sync
```

#### INCREMENTAL:
```
1. Buscar last_incremental_sync ou last_full_sync
   ↓
2. Se não existe → executar COMPLETA
   ↓
3. Buscar vagas da API
   ├─ Compara cada vaga: data_API > data_BD?
   └─ Atualiza apenas se mudou
   ↓
4. Buscar talentos modificados após last_sync
   ├─ Filtro: updatedAt >= last_sync
   └─ Compara: data_API > data_BD
   ↓
5. Atualizar last_incremental_sync
```

---

### Lógica de Comparação de Datas

**AMBAS** usam a mesma lógica de comparação:

```python
# Para cada registro (Vaga, Talento, Posição):
if existing_record:
    if api_updatedAt and db_updated_at_inhire:
        normalized_date = normalize_datetime(api_updatedAt)

        if normalized_date <= db_updated_at_inhire:
            return 'skipped'  # NÃO ATUALIZA

    # Se chegou aqui: data_API > data_BD
    # Atualiza o registro
    return 'updated'
```

**Em outras palavras:**
- ✅ `data_API > data_BD` → **ATUALIZA**
- ⏭️ `data_API <= data_BD` → **SKIP**

---

## Comandos de Execução

### Sincronização Completa

```bash
# Opção 1: Script dedicado
python sync_completa.py

# Opção 2: Script genérico
python run_sync.py --full
```

**Saída esperada:**
```
======================================================================
 SINCRONIZAÇÃO COMPLETA - InHire
======================================================================

Banco:  inhire
Início: 2025-11-17 10:30:00 -03

AVISO: Sincronização completa pode demorar ~55 minutos
       Volume estimado: ~104.558 registros

Ordem de sincronização:
  1. Vagas (todas)
  2. Posições (todas, de cada vaga)
  3. Candidaturas (todas, de cada vaga)
  4. Talentos (apenas dos IDs coletados das candidaturas)

[1/3] Conectando ao banco de dados...
      [OK] Conexão estabelecida

[2/3] Inicializando serviço de sincronização...
      [OK] Serviço inicializado

[3/3]Executando sincronização completa...

      Isso pode levar vários minutos...
      Aguarde enquanto processamos todos os dados da API...

======================================================================
 RESULTADO
======================================================================
[OK] Sincronização completa FINALIZADA COM SUCESSO!

----------------------------------------------------------------------
 ESTATÍSTICAS
----------------------------------------------------------------------
  Processados:  104,558
  Criados:      104,558
  Atualizados:  0
  Ignorados:    0
  Falhas:       0
----------------------------------------------------------------------

Tempo total: 3312.5s (55.2 minutos)

Término: 2025-11-17 11:25:00 -03
```

---

### Sincronização Incremental

```bash
# Opção 1: Script dedicado
python sync_incremental.py

# Opção 2: Script genérico
python run_sync.py --incremental
```

**Saída esperada:**
```
======================================================================
 SINCRONIZAÇÃO INCREMENTAL - InHire
======================================================================

Banco:  inhire
Início: 2025-11-17 14:00:00 -03

[1/4] Conectando ao banco de dados...
      [OK] Conexão estabelecida

[2/4] Verificando última sincronização...
      [OK] Última sync: 2025-11-17 11:25:00 -03

      Sincronizará apenas registros modificados após essa data.

[3/4] Inicializando serviço de sincronização...
      [OK] Serviço inicializado

[4/4] Executando sincronização incremental...

      Lógica de atualização:
        - Registro não existe no BD → CRIA
        - Registro existe:
          * data_API > data_BD → ATUALIZA
          * data_API <= data_BD → SKIP (já atualizado)

======================================================================
 RESULTADO
======================================================================
[OK] Sincronização incremental FINALIZADA COM SUCESSO!

----------------------------------------------------------------------
 ESTATÍSTICAS
----------------------------------------------------------------------
  Processados:  250
  Criados:      15
  Atualizados:  35
  Ignorados:    200
  Falhas:       0
----------------------------------------------------------------------

Tempo total: 125.3s (2.09 minutos)

Término: 2025-11-17 14:02:05 -03

Eficiência: 80.0% dos registros já estavam atualizados
```

---

## Quando Usar Cada Uma

### Use SINCRONIZAÇÃO COMPLETA quando:

- ✅ É a **primeira vez** sincronizando
- ✅ Quer garantir que **todos** os dados estão sincronizados
- ✅ Houve **mudanças estruturais** no banco ou API
- ✅ Quer sincronizar **Posições e Candidaturas**
- ✅ Pode aguardar **~55 minutos**
- ✅ Execução **mensal** ou **sob demanda**

### Use SINCRONIZAÇÃO INCREMENTAL quando:

- ✅ Já fez sincronização completa antes
- ✅ Quer apenas dados **novos/modificados**
- ✅ Precisa de **velocidade** (2-5 min)
- ✅ Execução **diária** ou **horária** (automática)
- ✅ Foco em **Vagas e Talentos**

---

## Estratégia Recomendada

### Agendamento Ideal

```
┌─────────────────────────────────────────────────────────────┐
│ PRIMEIRA VEZ:                                               │
│   python sync_completa.py                                   │
│   (aguardar ~55 minutos)                                    │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ ROTINA AUTOMÁTICA (scheduler.py):                          │
│                                                             │
│   - Incremental: A cada 60 minutos                         │
│     python sync_incremental.py                             │
│                                                             │
│   - Completa: 1x por mês (ou 1x por semana)                │
│     python sync_completa.py                                │
│     (às 02:00 AM de domingo)                               │
└─────────────────────────────────────────────────────────────┘
```

### Configurar Agendador

```bash
# Iniciar agendador automático
python scheduler.py
```

**Arquivo:** `scheduler.py`
```python
# Incremental a cada 60 minutos
scheduler.add_job(
    sync_incremental,
    'interval',
    minutes=60,
    id='sync_incremental'
)

# Completa diariamente às 02:00
scheduler.add_job(
    sync_full,
    'cron',
    hour=2,
    minute=0,
    id='sync_full'
)
```

---

## Arquivos Criados

| Arquivo | Descrição | Uso |
|---------|-----------|-----|
| `sync_completa.py` | Script standalone para sync completa | `python sync_completa.py` |
| `sync_incremental.py` | Script standalone para sync incremental | `python sync_incremental.py` |
| `run_sync.py` | Script genérico (ambos modos) | `python run_sync.py --full` ou `--incremental` |
| `scheduler.py` | Agendador automático | `python scheduler.py` |

---

## Resumo Visual

```
SINCRONIZAÇÃO COMPLETA
======================
API Inhire                          PostgreSQL
┌─────────────┐                    ┌─────────────┐
│ TODAS Vagas │ ────────────────>  │ Vagas       │
│ 100 registros│                    │ 100 records │
└─────────────┘                    └─────────────┘

┌──────────────┐                   ┌──────────────┐
│ TODAS Posições│ ──────────────>  │ Posições     │
│ 500 registros │                   │ 500 records  │
└──────────────┘                   └──────────────┘

┌────────────────┐                 ┌────────────────┐
│ TODAS Candidat.│ ──────────────> │ Candidaturas   │
│ 1.500 registros│                 │ 1.500 records  │
└────────────────┘                 └────────────────┘

┌────────────────┐                 ┌────────────────┐
│ Talentos (IDs) │ ──────────────> │ Talentos       │
│ 800 registros  │                 │ 800 records    │
└────────────────┘                 └────────────────┘

Tempo: ~55 minutos
Total: 2.900 registros


SINCRONIZAÇÃO INCREMENTAL
=========================
Última sync: 2025-11-17 10:00:00

API Inhire                          PostgreSQL
┌─────────────┐                    ┌─────────────┐
│ Vagas       │ ─── Compara ────>  │ Vagas       │
│ updatedAt   │     data_API vs    │ updated_at  │
│ > 10:00     │     data_BD        │             │
└─────────────┘                    └─────────────┘
     │                                     │
     └─> 15 modificadas                   └─> 10 atualizadas
         5 novas                               5 criadas
         80 sem mudanças                       80 ignoradas

┌────────────────┐                 ┌────────────────┐
│ Talentos       │ ─── Compara ─>  │ Talentos       │
│ updatedAt      │     data_API vs │                │
│ > 10:00        │     data_BD     │                │
└────────────────┘                 └────────────────┘
     │                                     │
     └─> 25 modificados                   └─> 20 atualizados
         5 novos                               5 criados

Tempo: ~2-5 minutos
Total: 130 registros processados
       40 atualizados/criados
       80 ignorados (já atualizados)
```

---

## Conclusão

Ambas as sincronizações usam a **mesma lógica de comparação** (`data_API > data_BD`), mas:

- **Completa:** Busca TUDO e compara individualmente (mais lento, mais completo)
- **Incremental:** Busca apenas modificados e compara (mais rápido, focado)

Para o dia a dia, use **incremental** e rode **completa** periodicamente para garantir consistência.
