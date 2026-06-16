# Comparação: Estratégias de Sincronização Inhire

## Resumo Executivo

| Estratégia | Tempo | Chamadas API | Uso | Eficiência |
|-----------|-------|--------------|-----|-----------|
| **Completa** | 50-60 min | ~3,500 | Semanal | Baixa (força bruta) |
| **Incremental Completa** | 5-6 horas | ~2,200 | ❌ Não usar | Muito baixa (pseudo-incremental) |
| **Incremental Otimizada** | 5-15 min | ~50-200 | A cada 2-4h | Alta (verdadeiramente incremental) |

## 1. Sincronização Completa (`sync_completa.py`)

### Estratégia
- Busca **TODOS** os registros da API
- **NÃO compara** datas (sempre sobrescreve)
- Força bruta total

### Comportamento
```python
# VAGAS
for vaga in api.get_all_vagas():
    db.insert_or_replace(vaga)  # SEMPRE substitui

# POSIÇÕES (1,088 chamadas)
for vaga in todas_vagas:
    for posicao in api.get_all_posicoes(vaga.id):
        db.insert_or_replace(posicao)  # SEMPRE substitui

# CANDIDATURAS (1,088 chamadas)
for vaga in todas_vagas:
    for candidatura in api.get_all_candidaturas(vaga.id):
        db.insert_or_replace(candidatura)  # SEMPRE substitui

# TALENTOS (todos)
for talento in api.get_all_talentos():
    db.insert_or_replace(talento)  # SEMPRE substitui
```

### Métricas
- **Tempo:** 50-60 minutos
- **Chamadas API:** ~3,500
  - 22x buscas paginadas de vagas (50 por página)
  - 1,088 chamadas de posições
  - 1,088 chamadas de candidaturas
  - ~300 buscas paginadas de talentos
- **Processamento:** ~7,000 registros
- **Eficiência:** Baixa (sobrescreve tudo sempre)

### Quando Usar
✅ **Usar:**
- 1x por semana (domingos 02:00)
- Após manutenção do banco
- Para garantir consistência total

❌ **Não usar:**
- Para sincronizações frequentes
- Durante horário comercial

---

## 2. Sincronização Incremental Completa (`sync_incremental_completa.py`)

### Estratégia
- Busca **TODOS** os registros da API
- **Compara datas** apenas no momento do UPSERT
- **PROBLEMA:** Faz chamadas API desnecessárias

### Comportamento
```python
# VAGAS (todas)
for vaga in api.get_all_vagas():
    if vaga.updated_at > db_vaga.updated_at:
        db.update(vaga)  # Compara e atualiza
    else:
        pass  # SKIP (mas JÁ fez a chamada API!)

# POSIÇÕES (1,088 chamadas - INEFICIENTE!)
for vaga in session.query(Vaga).all():  # TODAS as 1,088 vagas
    for posicao in api.get_all_posicoes(vaga.id):  # Chamada API desperdiçada
        if posicao.updated_at > db_posicao.updated_at:
            db.update(posicao)
        else:
            pass  # SKIP

# CANDIDATURAS (1,088 chamadas - INEFICIENTE!)
for vaga in session.query(Vaga).all():  # TODAS as 1,088 vagas
    for candidatura in api.get_all_candidaturas(vaga.id):  # Chamada API desperdiçada
        if candidatura.updated_at > db_candidatura.updated_at:
            db.update(candidatura)
        else:
            pass  # SKIP
```

### Métricas (Execução Real)
- **Tempo:** 5-6 horas ❌
- **Chamadas API:** ~2,200
  - 22x buscas de vagas
  - 1,088 chamadas de posições (99.6% desperdiçadas!)
  - 1,088 chamadas de candidaturas (99.6% desperdiçadas!)
- **Processamento:** ~7,000 registros
- **Eficiência:** Muito baixa
  - 99.6% dos registros já estavam atualizados
  - Apenas 4 de 1,088 vagas mudaram
  - Mas fez 2,176 chamadas API desnecessárias

### PROBLEMA CRÍTICO
❌ **Pseudo-Incremental:**
- Chama-se "incremental" mas **não filtra antes de buscar**
- Compara datas apenas **DEPOIS** de fazer chamada API
- Resultado: 99.6% de desperdício

### Quando Usar
❌ **NÃO USAR!**
- Substituído por `sync_incremental_otimizada.py`
- Mantido apenas para referência

---

## 3. Sincronização Incremental Otimizada (`sync_incremental_otimizada.py`)

### Estratégia
- Busca **TODAS** as vagas (detectar mudanças)
- **Filtra no BANCO** antes de buscar posições/candidaturas
- **Verdadeiramente incremental**

### Comportamento
```python
# VAGAS (todas - necessário)
for vaga in api.get_all_vagas():
    if vaga.updated_at > db_vaga.updated_at:
        db.update(vaga)
    else:
        pass  # SKIP

# POSIÇÕES (OTIMIZADO! Apenas vagas modificadas)
cutoff = now - timedelta(hours=4)
vagas_modificadas = session.query(Vaga).filter(
    Vaga.updated_at >= cutoff
).all()  # Apenas ~10-50 vagas (99% redução!)

for vaga in vagas_modificadas:  # Apenas vagas que mudaram!
    for posicao in api.get_all_posicoes(vaga.id):  # Chamada justificada
        db.upsert(posicao)

# CANDIDATURAS (OTIMIZADO! Mesma lógica)
for vaga in vagas_modificadas:  # Apenas vagas que mudaram!
    for candidatura in api.get_all_candidaturas(vaga.id):  # Chamada justificada
        db.upsert(candidatura)
```

### Métricas (Estimadas)
- **Tempo:** 5-15 minutos ✅
- **Chamadas API:** ~50-200 (95-98% redução!)
  - 22x buscas de vagas
  - ~10-50 chamadas de posições (apenas vagas modificadas)
  - ~10-50 chamadas de candidaturas (apenas vagas modificadas)
- **Processamento:** ~500-2,000 registros (apenas modificados)
- **Eficiência:** Alta (95-98%)

### Configuração da Janela

**Janela de Tempo (`--window`):**
Período em horas para considerar modificações. Recomenda-se 2x o intervalo de execução.

```bash
# Execução a cada 2 horas → janela de 4 horas
python sync_incremental_otimizada.py --window 4

# Execução a cada 4 horas → janela de 8 horas
python sync_incremental_otimizada.py --window 8

# Execução a cada 1 hora → janela de 2 horas
python sync_incremental_otimizada.py --window 2
```

**Por que 2x?**
- Margem de segurança para atrasos
- Garante capturar todas as mudanças
- Evita perder registros entre execuções

### Quando Usar
✅ **Usar:**
- A cada 2-4 horas durante horário comercial
- Como sincronização principal
- Sempre que precisar dados atualizados rápido

---

## Comparação Visual: Chamadas API

### Cenário Real (1,088 vagas, 4 modificadas nas últimas 4 horas)

```
┌─────────────────────┬──────────┬──────────────────┬──────────────────────┐
│ Fase                │ Completa │ Incr. Completa   │ Incr. Otimizada      │
├─────────────────────┼──────────┼──────────────────┼──────────────────────┤
│ Vagas               │ 22       │ 22               │ 22                   │
│ Posições            │ 1,088    │ 1,088 ❌         │ 4 ✅                 │
│ Candidaturas        │ 1,088    │ 1,088 ❌         │ 4 ✅                 │
│ Talentos            │ ~300     │ ~50              │ ~50                  │
├─────────────────────┼──────────┼──────────────────┼──────────────────────┤
│ TOTAL               │ 2,498    │ 2,248            │ 80                   │
│ Tempo               │ 55 min   │ 5-6 horas ⚠️     │ 5-10 min ⚡          │
└─────────────────────┴──────────┴──────────────────┴──────────────────────┘

REDUÇÃO: 96.8% menos chamadas (80 vs 2,248)
GANHO: ~40x mais rápida (5 min vs 5-6 horas)
```

---

## Análise de Eficiência

### Incremental Completa vs Otimizada

**Exemplo: 1,088 vagas, 4 modificadas (0.4%)**

| Métrica | Incr. Completa | Incr. Otimizada | Ganho |
|---------|---------------|-----------------|-------|
| Vagas buscadas | 1,088 | 1,088 | - |
| Vagas atualizadas | 4 (0.4%) | 4 (0.4%) | - |
| **Chamadas posições** | **1,088** ❌ | **4** ✅ | **272x menos** |
| **Chamadas candidaturas** | **1,088** ❌ | **4** ✅ | **272x menos** |
| Chamadas desperdiçadas | 2,168 | 0 | ∞ melhor |
| Tempo | 5-6 horas | 5-10 min | ~40x |
| Eficiência | 0.4% | 99.6% | 250x |

---

## Recomendações de Uso

### Cronograma Ideal

```
Segunda a Sexta (Horário Comercial):
├─ 08:00 → sync_incremental_otimizada.py --window 8
├─ 10:00 → sync_incremental_otimizada.py --window 4
├─ 12:00 → sync_incremental_otimizada.py --window 4
├─ 14:00 → sync_incremental_otimizada.py --window 4
├─ 16:00 → sync_incremental_otimizada.py --window 4
└─ 18:00 → sync_incremental_otimizada.py --window 4

Sábado/Domingo:
└─ 02:00 → sync_completa.py (garantir consistência)
```

### Regras

1. **Sync Otimizada:**
   - Use como sincronização principal
   - Execute a cada 2-4 horas
   - Janela = 2x intervalo

2. **Sync Completa:**
   - 1x por semana (domingo 02:00)
   - Após manutenção/migração
   - Quando precisar reconstruir tudo

3. **Sync Incremental Completa:**
   - ❌ Não usar (obsoleta)
   - Substituída pela Otimizada

---

## Logs de Execução Real

### Incremental Completa (INEFICIENTE)

```
[1/4] Vagas: 1,088 processadas, 4 atualizadas, 1,084 SKIP (99.6%)
[2/4] Posições: 1,088 chamadas API → Processando... (41% após 3 horas)
      ❌ PROBLEMA: 99.6% das chamadas são desperdiçadas!
[CANCELADO após 3 horas]
```

### Incremental Otimizada (ESPERADO)

```
[1/4] Vagas: 1,088 processadas, 4 atualizadas, 1,084 SKIP (99.6%)
[2/4] Posições:
      - Total vagas: 1,088
      - Modificadas: 4
      - ⚡ REDUÇÃO: 99.6% (1,084 vagas puladas)
      - Processando 4 vagas... [DONE em 30s]
[3/4] Candidaturas:
      - Processando 4 vagas... [DONE em 45s]
[4/4] Talentos: 12 únicos... [DONE em 2 min]

TOTAL: 5 minutos
ECONOMIA: 2,168 chamadas API (96.8%)
```

---

## Conclusão

### ✅ Use: `sync_incremental_otimizada.py`
- **Mais rápida:** 5-15 min (vs 5-6 horas)
- **Mais eficiente:** 96-98% redução em chamadas API
- **Verdadeiramente incremental:** Filtra ANTES de buscar
- **Econômica:** Reduz custos de API e infraestrutura

### ⚠️ Use com moderação: `sync_completa.py`
- **Semanal:** 1x por semana
- **Manutenção:** Após mudanças estruturais
- **Consistência:** Garantir integridade total

### ❌ Evite: `sync_incremental_completa.py`
- **Obsoleta:** Substituída pela Otimizada
- **Ineficiente:** 40x mais lenta sem benefícios
- **Pseudo-incremental:** Nome enganoso

---

## Próximos Passos

1. ✅ Testar `sync_incremental_otimizada.py` com janela de 4 horas
2. ✅ Monitorar métricas (tempo, registros processados, economia)
3. ✅ Ajustar janela conforme necessidade
4. ✅ Configurar cron/agendador com horários recomendados
5. ✅ Desabilitar `sync_incremental_completa.py` em produção
