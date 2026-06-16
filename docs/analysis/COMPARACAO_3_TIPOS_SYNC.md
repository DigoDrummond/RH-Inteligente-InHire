# Comparação: 3 Tipos de Sincronização

## Visão Geral

| Tipo | Arquivo | Entidades | Tempo | Quando Usar |
|------|---------|-----------|-------|-------------|
| **Completa** | `sync_completa.py` | Todas (100%) | ~55 min | 1ª vez, mensal |
| **Incremental Simples** | `sync_incremental.py` | Vagas + Talentos | ~2-5 min | Horária (atual) |
| **Incremental Completa** | `sync_incremental_completa.py` | Todas (100%) | ~10-20 min | A cada 2-4h (RECOMENDADA) |

---

## Detalhamento por Tipo

### 1. SYNC COMPLETA

**Arquivo:** `sync_completa.py`

**O que faz:**
```
├─ Vagas: TODAS da API
├─ Posições: TODAS (de cada vaga)
├─ Candidaturas: TODAS (de cada vaga)
└─ Talentos: IDs coletados das candidaturas
```

**Comparação de datas:**
- ✅ Sim (em todas as entidades)
- Mas busca TUDO da API primeiro, depois compara

**Comando:**
```bash
python sync_completa.py
```

**Características:**
- ✅ Sincroniza 100% dos dados
- ✅ Garante consistência total
- ✅ Compara datas (pula não modificados)
- ⏱️ Lenta (~55 minutos)

**Volume estimado:**
- ~100 vagas
- ~500 posições
- ~1.500 candidaturas
- ~800 talentos
- **Total: ~2.900 registros**

**Quando usar:**
- Primeira vez (carga inicial)
- 1x por mês (manutenção)
- Após mudanças estruturais

---

### 2. SYNC INCREMENTAL SIMPLES

**Arquivo:** `sync_incremental.py`

**O que faz:**
```
├─ Vagas: TODAS (compara datas)
├─ Posições: ❌ NÃO sincroniza
├─ Candidaturas: ❌ NÃO sincroniza
└─ Talentos: Apenas modificados (filter)
```

**Comparação de datas:**
- ✅ Vagas: compara individualmente
- ✅ Talentos: tenta filtro na API + compara

**Comando:**
```bash
python sync_incremental.py
```

**Características:**
- ✅ Muito rápida (~2-5 minutos)
- ✅ Leve e eficiente
- ❌ NÃO sincroniza Posições/Candidaturas
- ⚠️ Dados de Posições/Candidaturas desatualizados até próxima full

**Volume típico:**
- ~100 vagas (compara todas)
- ~15-50 talentos modificados
- **Total: ~115-150 registros**

**Quando usar:**
- Ambiente de baixa mudança
- Posições/Candidaturas mudam raramente
- Sync Completa frequente (diária)

**Limitação:**
```
10:00 - Candidato muda de etapa "Triagem" → "Entrevista"
11:00 - Sync Incremental Simples executa
        └─ Candidatura NÃO atualiza ❌
02:00 - Sync Completa executa
        └─ Candidatura FINALMENTE atualiza ✓

Desatualização: até 15 horas
```

---

### 3. SYNC INCREMENTAL COMPLETA ⭐ (NOVA)

**Arquivo:** `sync_incremental_completa.py`

**O que faz:**
```
├─ Vagas: TODAS (compara datas)
├─ Posições: TODAS as vagas (compara datas)
├─ Candidaturas: TODAS as vagas (compara datas*)
└─ Talentos: IDs coletados das candidaturas

* Requer correção em upsert_candidatura()
```

**Comparação de datas:**
- ✅ Vagas: compara `data_API > data_BD`
- ✅ Posições: compara `data_API > data_BD`
- ⚠️ Candidaturas: **precisa de correção** (atualmente sempre atualiza)
- ✅ Talentos: compara `data_API > data_BD`

**Comando:**
```bash
python sync_incremental_completa.py
```

**Características:**
- ✅ Sincroniza TODAS as entidades (100%)
- ✅ Compara datas (eficiente)
- ✅ Captura mudanças em TODOS os tipos de vagas
- ✅ Posições e Candidaturas sempre atualizadas
- ⚡ Mais rápida que Completa (~10-20 min vs ~55 min)
- ⏱️ Mais lenta que Simples (~10-20 min vs ~2-5 min)

**Volume típico:**
```
Primeira execução (após full):
  Processados: ~2.900
  Criados: 0
  Atualizados: ~200 (apenas modificados)
  Ignorados: ~2.700 (não mudaram)

Execuções subsequentes:
  Processados: ~2.900
  Criados: ~10 (novos)
  Atualizados: ~50-100 (modificados)
  Ignorados: ~2.800 (não mudaram)
```

**Quando usar:**
- Ambiente de produção
- Dados precisam estar sempre atualizados
- A cada 2-4 horas
- **RECOMENDADA para uso contínuo**

---

## Comparação Lado a Lado

### Entidades Sincronizadas

| Entidade | Completa | Incremental Simples | Incremental Completa |
|----------|----------|---------------------|----------------------|
| **Vagas** | ✅ Todas | ✅ Todas (compara) | ✅ Todas (compara) |
| **Posições** | ✅ Todas | ❌ Não | ✅ **Todas (compara)** |
| **Candidaturas** | ✅ Todas | ❌ Não | ✅ **Todas (compara*)** |
| **Talentos** | ✅ IDs coletados | ✅ Modificados | ✅ IDs coletados |

---

### Performance

| Aspecto | Completa | Incremental Simples | Incremental Completa |
|---------|----------|---------------------|----------------------|
| **Tempo** | ~55 min | ~2-5 min | ~10-20 min |
| **Registros** | ~2.900 | ~115-150 | ~2.900 |
| **Atualizados** | Todos modificados | Vagas + Talentos | Todos modificados |
| **Pula (SKIP)** | ✅ Sim | ✅ Sim | ✅ Sim |
| **Eficiência** | Baixa (busca tudo) | Alta (só 2 entidades) | Média (busca tudo, compara) |

---

### Atualização de Dados

**Cenário:** Candidato muda de etapa às 10:00

| Tipo | Detecta mudança? | Quando atualiza? | Delay |
|------|------------------|------------------|-------|
| Completa | ✅ Sim | Na próxima exec (02:00) | ~16 horas |
| Incremental Simples | ❌ Não | Próxima Completa (02:00 dia seguinte) | ~40 horas |
| Incremental Completa | ✅ Sim | Próxima exec (a cada 2-4h) | ~2-4 horas |

---

## Estratégia Recomendada

### Opção A: Produção (Alta Frequência) ⭐

```
CARGA INICIAL (1x):
  └─ python sync_completa.py (~55 min)

ROTINA DIÁRIA:
  ├─ Incremental Completa: A cada 2 horas (07:00, 09:00, 11:00, ..., 19:00)
  │  └─ python sync_incremental_completa.py (~10-20 min)
  │
  └─ Completa: 1x por semana (domingo 02:00)
     └─ python sync_completa.py (~55 min)
```

**Configurar scheduler:**
```python
# scheduler.py

# Incremental Completa a cada 2 horas (horário comercial)
scheduler.add_job(
    sync_incremental_completa,
    'cron',
    hour='7-19/2',  # 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00
    id='sync_incremental_completa'
)

# Completa 1x por semana (domingo 02:00)
scheduler.add_job(
    sync_completa,
    'cron',
    day_of_week='sun',
    hour=2,
    minute=0,
    id='sync_completa_semanal'
)
```

**Características:**
- ✅ Dados sempre atualizados (delay máximo: 2h)
- ✅ Sincroniza TUDO (100% entidades)
- ✅ Eficiente (pula não modificados)
- ⚡ Executa fora de horário de pico

---

### Opção B: Desenvolvimento (Baixa Frequência)

```
CARGA INICIAL (1x):
  └─ python sync_completa.py (~55 min)

ROTINA DIÁRIA:
  ├─ Incremental Simples: A cada hora (rápida)
  │  └─ python sync_incremental.py (~2-5 min)
  │
  └─ Completa: Diariamente 02:00
     └─ python sync_completa.py (~55 min)
```

**Configurar scheduler:**
```python
# Incremental Simples a cada hora
scheduler.add_job(
    sync_incremental_simples,
    'interval',
    hours=1,
    id='sync_incremental_simples'
)

# Completa diária 02:00
scheduler.add_job(
    sync_completa,
    'cron',
    hour=2,
    minute=0,
    id='sync_completa_diaria'
)
```

**Características:**
- ⚡ Muito rápida (2-5 min)
- ⚠️ Posições/Candidaturas podem estar desatualizadas
- ✅ Sync Completa diária garante consistência
- 💰 Menos carga no servidor

---

## Correção Necessária

### Para usar Incremental Completa:

**Aplicar correção em `database_service.py`:**

```python
# services/database_service.py (linha ~214)

def upsert_candidatura(self, cand_api, job_id):
    existing = self.session.query(Candidatura).filter_by(inhire_id=cand_api.id).first()

    if existing:
        # ✅ ADICIONAR COMPARAÇÃO DE DATA
        if cand_api.updatedAt and existing.updated_at_inhire:
            updated_at_normalized = self._normalize_datetime(cand_api.updatedAt)
            if updated_at_normalized <= existing.updated_at_inhire:
                return False, 'skipped'  # Pula se não mudou

        # ... resto do código
```

**Após correção:**
- ✅ Candidaturas comparação datas
- ✅ Pula candidaturas não modificadas
- ✅ Mais eficiente

---

## Resumo Final

### Para seu caso (quer comparar TUDO):

**Use:** `sync_incremental_completa.py` ⭐

**Motivos:**
1. ✅ Sincroniza **TODAS** as vagas (fechadas, abertas, canceladas, etc.)
2. ✅ Sincroniza **TODAS** as posições (de todas as vagas)
3. ✅ Sincroniza **TODAS** as candidaturas (de todas as vagas)
4. ✅ Compara datas em cada registro (eficiente)
5. ✅ Captura mudanças em qualquer tipo de vaga/posição
6. ⚡ Mais rápida que Completa (~10-20 min vs ~55 min)

**Próximos passos:**
1. Aplicar correção em `upsert_candidatura()`
2. Testar `sync_incremental_completa.py`
3. Configurar scheduler para executar a cada 2-4 horas

---

**Quer que eu aplique a correção e teste?** 🚀
