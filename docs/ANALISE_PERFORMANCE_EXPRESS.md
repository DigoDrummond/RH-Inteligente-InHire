# 📊 Análise de Performance - SYNC EXPRESS

**Objetivo:** Monitorar e otimizar a performance do SYNC EXPRESS

---

## 🎯 KPIs Principais

### Tempo de Execução
| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| Tempo total | < 5 min | ⏳ Medindo | - |
| Tempo por vaga | < 13s | ⏳ Medindo | - |
| Tempo por candidatura | < 50ms | ⏳ Medindo | - |
| Tempo por talento | < 100ms | ⏳ Medindo | - |

### Volume de Dados
| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| Vagas processadas | ~23 | 23 ✅ | OK |
| Candidaturas | ~500-1.000 | ⏳ Medindo | - |
| Talentos únicos | ~300-600 | ⏳ Medindo | - |

### API e Rede
| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| Total de requests | < 100 | ⏳ Medindo | - |
| Rate limit atingido | 0 | ⏳ Medindo | - |
| Tempo de resposta médio | < 500ms | ⏳ Medindo | - |
| Timeouts | 0 | ⏳ Medindo | - |

### Qualidade de Dados
| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| Taxa de sucesso | > 99% | ⏳ Medindo | - |
| Erros críticos | 0 | 0 ✅ | OK |
| FK órfãos (após talentos) | 0 | ⏳ Medindo | - |
| Constraint violations | 0 | 0 ✅ | OK |

---

## 📈 Queries de Monitoramento

### 1. Tempo de Execução por Sync
```sql
-- Últimos 10 syncs EXPRESS/INCREMENTAL
SELECT
    id,
    sync_type,
    status,
    TO_CHAR(start_time, 'YYYY-MM-DD HH24:MI:SS') AS inicio,
    TO_CHAR(end_time, 'YYYY-MM-DD HH24:MI:SS') AS fim,
    ROUND(EXTRACT(EPOCH FROM (end_time - start_time))/60, 2) AS duracao_min,
    records_processed AS processados,
    records_created AS criados,
    records_updated AS atualizados,
    records_failed AS falhas
FROM sync_log
WHERE sync_type IN ('EXPRESS', 'INCREMENTAL')
ORDER BY start_time DESC
LIMIT 10;
```

### 2. Comparativo EXPRESS vs INCREMENTAL vs FULL
```sql
-- Médias dos últimos 30 dias
SELECT
    sync_type,
    COUNT(*) AS total_execucoes,
    ROUND(AVG(EXTRACT(EPOCH FROM (end_time - start_time))/60), 2) AS tempo_medio_min,
    ROUND(MIN(EXTRACT(EPOCH FROM (end_time - start_time))/60), 2) AS tempo_min_min,
    ROUND(MAX(EXTRACT(EPOCH FROM (end_time - start_time))/60), 2) AS tempo_max_min,
    SUM(records_processed) AS total_processados,
    ROUND(AVG(records_processed), 0) AS media_processados,
    ROUND(AVG(records_created), 0) AS media_criados,
    ROUND(AVG(records_updated), 0) AS media_atualizados,
    SUM(records_failed) AS total_falhas
FROM sync_log
WHERE start_time > NOW() - INTERVAL '30 days'
  AND status != 'ERROR'
GROUP BY sync_type
ORDER BY
    CASE sync_type
        WHEN 'EXPRESS' THEN 1
        WHEN 'INCREMENTAL' THEN 2
        WHEN 'FULL' THEN 3
    END;
```

### 3. Taxa de Atualização de Dados Críticos
```sql
-- Defasagem atual dos dados críticos
SELECT
    'Candidaturas' AS entidade,
    COUNT(*) AS total,
    COUNT(CASE WHEN updated_at_inhire > NOW() - INTERVAL '2 hours' THEN 1 END) AS atualizadas_2h,
    COUNT(CASE WHEN updated_at_inhire > NOW() - INTERVAL '4 hours' THEN 1 END) AS atualizadas_4h,
    ROUND(100.0 * COUNT(CASE WHEN updated_at_inhire > NOW() - INTERVAL '2 hours' THEN 1 END) / COUNT(*), 2) AS pct_frescos_2h
FROM candidaturas
WHERE vaga_id IN (
    SELECT DISTINCT vaga_id FROM posicoes WHERE status = 'open'
)

UNION ALL

SELECT
    'Talentos' AS entidade,
    COUNT(*) AS total,
    COUNT(CASE WHEN updated_at_inhire > NOW() - INTERVAL '2 hours' THEN 1 END) AS atualizadas_2h,
    COUNT(CASE WHEN updated_at_inhire > NOW() - INTERVAL '4 hours' THEN 1 END) AS atualizadas_4h,
    ROUND(100.0 * COUNT(CASE WHEN updated_at_inhire > NOW() - INTERVAL '2 hours' THEN 1 END) / COUNT(*), 2) AS pct_frescos_2h
FROM talentos
WHERE id IN (
    SELECT DISTINCT talento_id
    FROM candidaturas
    WHERE vaga_id IN (SELECT vaga_id FROM posicoes WHERE status = 'open')
      AND talento_id IS NOT NULL
);
```

### 4. Distribuição de Candidaturas por Vaga
```sql
-- Identificar vagas com muitas candidaturas (possível gargalo)
SELECT
    v.id,
    v.name,
    v.department,
    COUNT(c.id) AS total_candidaturas,
    COUNT(CASE WHEN c.status = 'active' THEN 1 END) AS candidaturas_ativas,
    MAX(c.updated_at_inhire) AS ultima_atualizacao
FROM vagas v
JOIN posicoes p ON v.id = p.vaga_id
LEFT JOIN candidaturas c ON c.vaga_id = v.id
WHERE p.status = 'open'
GROUP BY v.id, v.name, v.department
ORDER BY total_candidaturas DESC
LIMIT 20;
```

### 5. Erros e Warnings nos Últimos Syncs
```sql
-- Identificar padrões de erros
SELECT
    sync_type,
    TO_CHAR(start_time, 'YYYY-MM-DD HH24:MI') AS data_hora,
    status,
    records_failed,
    LEFT(error_message, 200) AS erro_resumo
FROM sync_log
WHERE (status = 'ERROR' OR records_failed > 0)
  AND start_time > NOW() - INTERVAL '7 days'
ORDER BY start_time DESC
LIMIT 20;
```

---

## 🔍 Pontos de Atenção para Análise

### Performance
1. **Vagas com Muitas Candidaturas**
   - Identificar vagas com > 100 candidaturas
   - Considerar paginação adicional ou processamento paralelo
   - Monitorar tempo por vaga

2. **Rate Limiting**
   - Verificar se há backoffs frequentes
   - Ajustar rate limiter se necessário
   - Considerar cache de respostas se aplicável

3. **Commits em Batch**
   - Avaliar se batch_size atual (50/100) é otimal
   - Testar com valores diferentes (25, 75, 150)
   - Balancear entre performance e segurança

### Qualidade de Dados
1. **FK Órfãos**
   - Verificar se todos são resolvidos após sync de talentos
   - Identificar talentos que nunca são encontrados
   - Considerar limpeza de candidaturas órfãs antigas

2. **Constraints**
   - Monitorar se novas violations aparecem
   - Validar datas antes de inserção
   - Log detalhado de casos edge

3. **Duplicações**
   - Verificar se há duplicações de candidaturas
   - Validar unicidade de inhire_id
   - Monitorar unique constraint violations

### Operacional
1. **Frequência de Execução**
   - Avaliar se 2h é adequado
   - Considerar horários de pico
   - Ajustar para horário comercial se necessário

2. **Concorrência**
   - Verificar se há sobreposição de syncs
   - Implementar lock para evitar execuções simultâneas
   - Monitorar pool de conexões do BD

3. **Alertas**
   - Definir thresholds para alertas
   - Configurar notificações de falhas
   - Dashboard de status em tempo real

---

## 📋 Checklist de Análise Semanal

### Segunda-feira
- [ ] Revisar logs da semana anterior
- [ ] Analisar tempo médio de execução
- [ ] Verificar taxa de erros
- [ ] Identificar gargalos

### Quarta-feira
- [ ] Verificar defasagem de dados
- [ ] Analisar distribuição de candidaturas
- [ ] Revisar FK órfãos
- [ ] Validar integridade referencial

### Sexta-feira
- [ ] Gerar relatório semanal
- [ ] Comparar KPIs com targets
- [ ] Documentar anomalias
- [ ] Propor otimizações

---

## 🎯 Metas de Otimização

### Curto Prazo (1-2 semanas)
1. **Baseline de Performance**
   - Coletar métricas por 1 semana
   - Estabelecer baseline de tempo e volume
   - Identificar padrões de uso

2. **Otimizações Rápidas**
   - Ajustar batch_size se necessário
   - Otimizar queries SQL se identificado
   - Configurar índices adicionais se benéfico

### Médio Prazo (1 mês)
1. **Cache Inteligente**
   - Cache de talentos frequentes
   - Cache de vagas ativas
   - TTL de 1h para dados quentes

2. **Processamento Paralelo**
   - Considerar threads para busca de candidaturas
   - Pool de workers para talentos
   - Manter ordem de commits

### Longo Prazo (3 meses)
1. **Arquitetura Assíncrona**
   - Message queue para jobs
   - Workers dedicados por tipo
   - Escalabilidade horizontal

2. **ML/Predição**
   - Prever volume de candidaturas
   - Ajustar recursos dinamicamente
   - Identificar anomalias automaticamente

---

## 📊 Template de Relatório Semanal

```markdown
# Relatório SYNC EXPRESS - Semana XX/2026

## Resumo Executivo
- Execuções: X
- Taxa de sucesso: XX%
- Tempo médio: X.X min
- Dados sincronizados: X.XXX registros

## Performance
- Tempo mínimo: X.X min
- Tempo máximo: X.X min
- Desvio padrão: X.X min
- Tendência: ↗ ↘ →

## Qualidade
- Erros totais: X
- FK órfãos: X
- Constraint violations: X
- Duplicações: X

## Ações Requeridas
1. [ ] Ação 1
2. [ ] Ação 2
3. [ ] Ação 3

## Observações
- Observação 1
- Observação 2
```

---

## 🚨 Alertas Configurados

### Críticos (Imediato)
- ❌ Sync com status ERROR
- ❌ Tempo de execução > 10 min
- ❌ Taxa de falhas > 5%
- ❌ Rate limit atingido > 3x

### Warnings (Revisar em 24h)
- ⚠️ Tempo de execução > 7 min
- ⚠️ FK órfãos > 100
- ⚠️ Desvio padrão tempo > 2 min
- ⚠️ Candidaturas duplicadas detectadas

### Informativos (Revisar semanalmente)
- ℹ️ Nova vaga com posição aberta
- ℹ️ Volume de candidaturas cresceu > 20%
- ℹ️ Tempo de resposta API aumentou
- ℹ️ Padrão de uso mudou

---

**Última Atualização:** 2026-01-22
**Próxima Revisão:** 2026-01-29
**Responsável:** Equipe de Dados
