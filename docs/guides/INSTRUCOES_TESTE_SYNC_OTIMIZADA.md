# Instruções: Testar Sincronização Incremental Otimizada

## ⚠️ Problema Detectado

O PostgreSQL parece estar travado ou com locks ativos. Antes de testar:

### 1. Verificar se o PostgreSQL está respondendo

```powershell
# Verificar se o serviço está rodando
Get-Service -Name postgresql*

# Se não estiver, iniciar:
Start-Service postgresql-x64-18
```

### 2. Verificar locks no banco

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "
SELECT
    pid,
    usename,
    application_name,
    state,
    query_start,
    LEFT(query, 50) as query
FROM pg_stat_activity
WHERE datname = 'inhire'
  AND state != 'idle'
ORDER BY query_start;
"
```

### 3. Se houver locks travados

```bash
# Identificar processos travados
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "
SELECT
    pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'inhire'
  AND pid != pg_backend_pid()
  AND state = 'idle in transaction'
  AND state_change < NOW() - INTERVAL '5 minutes';
"
```

---

## 📋 Testes a Executar

### Teste 1: Queries de Identificação (SQL)

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f test_sync_queries.sql
```

**O que valida:**
- ✅ Campos de data estão populados
- ✅ Queries identificam registros modificados
- ✅ Estimativa de eficiência da otimização

### Teste 2: Sincronização Otimizada (Manual)

```bash
# Adicionar diretório ao PYTHONPATH e executar
$env:PYTHONPATH = "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
python sync_incremental_optimized.py
```

**O que esperar:**
- ⏱️ Tempo: 2-5 minutos (vs 10-20 min atual)
- 📊 Logs mostram quantos registros foram modificados
- ✅ Sincronização completa sem erros

### Teste 3: Comparação de Performance

Antes de adotar a nova estratégia, execute as duas e compare:

```bash
# 1. Sync Atual
python sync_incremental_completa.py

# Anotar tempo e estatísticas

# 2. Sync Otimizada
python sync_incremental_optimized.py

# Comparar resultados
```

---

## 📊 Métricas para Validação

### Eficiência Esperada

Execute esta query para ver a eficiência:

```sql
WITH ultima_sync AS (
    SELECT COALESCE(last_incremental_sync, last_full_sync) as data_ref
    FROM sync_configuration
    LIMIT 1
),
totais AS (
    SELECT
        (SELECT COUNT(*) FROM vagas) as total_vagas,
        (SELECT COUNT(*) FROM posicoes) as total_posicoes,
        (SELECT COUNT(*) FROM candidaturas) as total_candidaturas,
        (SELECT COUNT(*) FROM talentos) as total_talentos
),
modificados AS (
    SELECT
        COUNT(DISTINCT CASE WHEN v.updated_at_inhire > us.data_ref OR v.created_at > us.data_ref THEN v.id END) as vagas_mod,
        COUNT(DISTINCT CASE WHEN p.updated_at_inhire > us.data_ref THEN p.id END) as posicoes_mod,
        COUNT(DISTINCT CASE WHEN c.updated_at_inhire > us.data_ref THEN c.id END) as candidaturas_mod,
        COUNT(DISTINCT CASE WHEN t.updated_at_inhire > us.data_ref THEN t.id END) as talentos_mod
    FROM ultima_sync us
    LEFT JOIN vagas v ON TRUE
    LEFT JOIN posicoes p ON TRUE
    LEFT JOIN candidaturas c ON TRUE
    LEFT JOIN talentos t ON TRUE
)
SELECT
    'TOTAL' as metrica,
    t.total_vagas + t.total_posicoes + t.total_candidaturas + t.total_talentos as registros,
    m.vagas_mod + m.posicoes_mod + m.candidaturas_mod + m.talentos_mod as modificados,
    ROUND(
        ((m.vagas_mod + m.posicoes_mod + m.candidaturas_mod + m.talentos_mod)::NUMERIC /
        NULLIF(t.total_vagas + t.total_posicoes + t.total_candidaturas + t.total_talentos, 0)) * 100,
        2
    ) as percentual_modificado
FROM totais t, modificados m;
```

**Interpretação:**
- `< 5% modificado` → **EXCELENTE** (95%+ skip)
- `5-10% modificado` → **MUITO BOM** (90%+ skip)
- `10-30% modificado` → **BOM** (70%+ skip)
- `> 30% modificado` → **RAZOÁVEL** (considerar sync completa)

---

## 🎯 Checklist de Validação

Antes de adotar em produção, verificar:

- [ ] PostgreSQL está respondendo normalmente
- [ ] Teste SQL executou sem erros
- [ ] Sync otimizada completou em < 10 minutos
- [ ] Contagens das tabelas estão corretas
- [ ] Eficiência está > 70% (percentual skip)
- [ ] Logs não mostram erros críticos
- [ ] Performance melhorou vs sync atual

---

## 🔧 Troubleshooting

### Erro: "No module named 'config'"

**Solução:**
```powershell
# PowerShell
$env:PYTHONPATH = "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
python sync_incremental_optimized.py
```

### PostgreSQL não responde

**Verificar:**
```bash
# Status do serviço
Get-Service postgresql-x64-18

# Reiniciar se necessário
Restart-Service postgresql-x64-18
```

### Queries SQL demoram muito

**Possível causa:** Locks no banco

**Solução:**
```sql
-- Ver queries rodando
SELECT pid, query, state
FROM pg_stat_activity
WHERE datname = 'inhire';

-- Matar processo travado (substituir PID)
SELECT pg_terminate_backend(12345);
```

---

## 📚 Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `sync_incremental_optimized.py` | Script principal da sync otimizada |
| `test_sync_queries.sql` | Testes SQL das queries |
| `docs/guides/ESTRATEGIA_SYNC_BASEADA_EM_TABELAS.md` | Documentação completa |
| `docs/changelogs/CHANGELOG_2026-02-11_SYNC_INCREMENTAL_OTIMIZADA.md` | Changelog detalhado |
| `QUICK_START_SYNC_OTIMIZADA.md` | Guia rápido |

---

## 🚀 Próximos Passos

1. **Resolver problema do PostgreSQL**
   - Verificar se está rodando
   - Eliminar locks
   - Validar conexão

2. **Executar Teste SQL**
   ```bash
   psql -U postgres -d inhire -f test_sync_queries.sql
   ```

3. **Executar Sync Otimizada**
   ```bash
   $env:PYTHONPATH = "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
   python sync_incremental_optimized.py
   ```

4. **Validar Resultados**
   - Comparar tempos
   - Verificar contagens
   - Analisar logs

5. **Adotar em Produção**
   - Atualizar scheduler
   - Configurar frequência (1-2h)
   - Monitorar execuções

---

## 💡 Dica

Se o percentual de registros modificados for > 30%, considere:
- Aumentar frequência de sync incremental
- Executar sync completa mais frequentemente
- Verificar se há problema nos timestamps do BD
