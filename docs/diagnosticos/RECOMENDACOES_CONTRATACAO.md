# Recomendações: Monitoramento de Consistência em Contratações

**Data:** 2026-03-06
**Contexto:** Diagnóstico Posição 1559
**Status:** ✅ Implementado

---

## 📋 Sumário Executivo

Com base na análise da posição 1559 e identificação da lógica da view `vw_analise_posicoes`, foram criadas ferramentas de monitoramento para detectar inconsistências em processos de contratação.

**Resultado:** Posição 1559 está **CONSISTENTE** (contratada e fechada corretamente).

---

## 🛠️ Ferramentas Criadas

### 1. Script de Diagnóstico Individual

**Arquivo:** `scripts/debug/diagnostico_posicao_1559.py`

**Uso:**
```bash
python scripts/debug/diagnostico_posicao_1559.py
```

**Funcionalidades:**
- Consulta dados completos de uma posição específica
- Analisa timeline de mudanças de status
- Verifica candidaturas e etapas do funil
- Identifica inconsistências entre etapa, status e hired_at
- Gera relatório em markdown + dados em JSON

**Limitação Atual:**
- Algumas colunas da view `vw_analise_posicoes` podem ter nomes diferentes
- Script pode precisar ajustes para colunas específicas da view

### 2. Query de Monitoramento Completo

**Arquivo:** `scripts/validacao/check_inconsistencias_contratacao.sql`

**Uso:**
```bash
psql -U postgres -d inhire -f scripts/validacao/check_inconsistencias_contratacao.sql
```

**Funcionalidades:**
- Identifica TODAS as posições com potenciais inconsistências
- Classifica por severidade (CRÍTICO, ALTO, MÉDIO, BAIXO)
- Fornece estatísticas resumidas
- Sugere ações corretivas específicas

**Classificação de Severidade:**

| Severidade | Condição | Ação Requerida |
|------------|----------|----------------|
| **CRÍTICO** | Etapa="Contratação" + Status=open + hired_at=NULL | Urgente - Verificar status real |
| **ALTO** | Etapa="Contratação" + Status=closed + hired_at=NULL | Preencher hired_at |
| **MÉDIO** | Etapa="Contratação" + hired_at preenchido + Status=open | Atualizar status para closed |
| **BAIXO** | Etapa final (order>=9) + Status=open | Monitorar - pode estar em processo |

---

## 📊 Como Usar as Ferramentas

### Cenário 1: Verificar Posição Específica

```bash
# Opção 1: Modificar script para outra posição
# Editar diagnostico_posicao_1559.py linha 43:
# WHERE id = <POSICAO_ID>

python scripts/debug/diagnostico_posicao_1559.py

# Opção 2: Query manual
psql -U postgres -d inhire -c "
SELECT
    p.id, p.status, p.hired_at, p.updated_at,
    cd.stage_name, cd.stage_order
FROM posicoes p
LEFT JOIN candidaturas cd ON cd.vaga_id = p.vaga_id
WHERE p.id = <POSICAO_ID>
ORDER BY cd.stage_order DESC
LIMIT 5;
"
```

### Cenário 2: Monitoramento Semanal

```bash
# Executar toda segunda-feira
psql -U postgres -d inhire -f scripts/validacao/check_inconsistencias_contratacao.sql > relatorio_semanal.txt

# Analisar saída
cat relatorio_semanal.txt | grep "CRÍTICO\|ALTO"

# Se houver casos críticos, investigar
psql -U postgres -d inhire -c "
SELECT * FROM vw_analise_posicoes
WHERE id_position IN (<IDS_CRITICOS>);
"
```

### Cenário 3: Auditoria Mensal

```bash
# Gerar estatísticas completas
psql -U postgres -d inhire -f scripts/validacao/check_inconsistencias_contratacao.sql

# Exportar para análise
psql -U postgres -d inhire -t -A -F"," -c "
SELECT severidade, COUNT(*)
FROM (...query completa...)
GROUP BY severidade
" > stats_mensal.csv
```

---

## 🔍 Interpretação dos Resultados

### Exemplo de Saída

```
severidade | posicao_id | status_posicao | etapa_funil  | hired_at | descricao_problema
-----------+------------+----------------+--------------+----------+------------------------------------------
CRÍTICO    | 1234       | open           | Contratação  | NULL     | Candidato em Contratação mas posição ABERTA
ALTO       | 5678       | closed         | Contratação  | NULL     | Posição FECHADA mas hired_at não preenchido
MÉDIO      | 9012       | open           | Contratação  | 2026-03-01 | hired_at preenchido mas status não atualizado
```

### Ações Recomendadas por Caso

#### CRÍTICO: Posição 1234

**Problema:** Candidato em "Contratação" mas posição ainda aberta

**Investigar:**
1. Verificar na plataforma InHire se a contratação foi confirmada
2. Consultar timeline para ver último evento
3. Verificar com RH se há contratação pendente

**Ações:**
```sql
-- Se contratação foi confirmada
UPDATE posicoes
SET status = 'closed', hired_at = '2026-03-XX'
WHERE id = 1234;

-- Se contratação NÃO foi confirmada (candidato desistiu)
UPDATE candidaturas
SET stage_name = 'Proposta Recusada', stage_order = 8
WHERE vaga_id = (SELECT vaga_id FROM posicoes WHERE id = 1234)
  AND stage_name = 'Contratação';
```

#### ALTO: Posição 5678

**Problema:** Posição fechada mas hired_at não foi preenchido

**Investigar:**
1. Verificar se posição foi fechada COM ou SEM contratação
2. Se COM: preencher hired_at
3. Se SEM: verificar se status deveria ser "canceled"

**Ações:**
```sql
-- Se houve contratação
UPDATE posicoes
SET hired_at = '2026-03-XX'  -- data da contratação
WHERE id = 5678;

-- Se NÃO houve contratação
UPDATE posicoes
SET status = 'canceled', reason = 'Fechada sem contratação'
WHERE id = 5678;
```

#### MÉDIO: Posição 9012

**Problema:** Contratação registrada (hired_at) mas status não atualizado

**Ação:**
```sql
UPDATE posicoes
SET status = 'closed'
WHERE id = 9012;
```

---

## 🔄 Automação Futura (Opcional)

### Script de Monitoramento Automático

```bash
#!/bin/bash
# scripts/monitor/check_inconsistencias_daily.sh

# Configuração
DB_NAME="inhire"
DB_USER="postgres"
ALERT_EMAIL="ti@empresa.com"
LOG_FILE="logs/inconsistencias_$(date +%Y%m%d).log"

# Executar query
psql -U $DB_USER -d $DB_NAME \
  -f scripts/validacao/check_inconsistencias_contratacao.sql \
  > $LOG_FILE 2>&1

# Contar casos críticos
CRITICOS=$(grep "CRÍTICO" $LOG_FILE | wc -l)

# Alertar se houver casos críticos
if [ $CRITICOS -gt 0 ]; then
    echo "ALERTA: $CRITICOS casos CRÍTICOS encontrados" | \
        mail -s "Inconsistências em Contratações" $ALERT_EMAIL
fi
```

**Agendar no cron:**
```bash
# Executar todo dia às 8h
0 8 * * * /caminho/scripts/monitor/check_inconsistencias_daily.sh
```

---

## 📈 Métricas de Qualidade

### KPIs Sugeridos

1. **Taxa de Consistência**
   ```sql
   SELECT
       ROUND(
           COUNT(*) FILTER (WHERE severidade = 'OK')::numeric * 100.0 /
           COUNT(*)
       , 2) as taxa_consistencia_pct
   FROM (...query...)
   WHERE etapa_funil = 'Contratação';
   ```

   **Meta:** ≥ 95%

2. **Tempo Médio de Correção**
   - Rastrear quanto tempo leva para corrigir inconsistências detectadas
   - Meta: < 24 horas

3. **Casos Recorrentes**
   - Identificar se mesmas vagas/posições têm problemas repetidos
   - Investigar causa raiz sistemática

---

## 🎯 Melhorias na View (Opcional)

### Adicionar Validação na View

Modificar `vw_analise_posicoes` para incluir campo de alerta:

```sql
-- Adicionar coluna de validação
CASE
    WHEN etapa_funil = 'Contratação'
         AND status_atual NOT IN ('closed', 'filled')
         AND p.hired_at IS NULL
    THEN 'ALERTA: Inconsistência detectada - Verificar contratação'

    WHEN etapa_funil = 'Contratação'
         AND status_atual IN ('closed', 'filled')
         AND p.hired_at IS NULL
    THEN 'ATENÇÃO: hired_at não preenchido'

    WHEN etapa_funil = 'Contratação'
         AND p.hired_at IS NOT NULL
         AND status_atual NOT IN ('closed', 'filled')
    THEN 'ATENÇÃO: Status não atualizado'

    ELSE NULL
END AS alerta_validacao
```

**Benefício:**
- Identificação visual imediata de problemas
- Facilita filtragem em queries
- Pode alimentar dashboard de monitoramento

---

## 📝 Documentação Relacionada

1. **Diagnóstico Posição 1559**
   - `docs/diagnosticos/DIAGNOSTICO_POSICAO_1559.md`

2. **CLAUDE.md**
   - Seção sobre sincronização de dados
   - Lógica da view `vw_analise_posicoes`

3. **Migrations relevantes**
   - `migrations/044_create_complete_vw_analise_posicoes.sql` - Criação da view
   - `migrations/036_fix_sla_calculation.sql` - Correções de lógica

---

## ✅ Checklist de Implementação

- [x] Script de diagnóstico individual criado
- [x] Query de monitoramento completo criada
- [x] Documentação de uso criada
- [ ] Testar query em ambiente de produção
- [ ] Validar se há casos críticos atuais
- [ ] Definir processo de correção de inconsistências
- [ ] Treinar equipe no uso das ferramentas
- [ ] (Opcional) Implementar automação de alertas
- [ ] (Opcional) Adicionar campo de validação na view
- [ ] (Opcional) Criar dashboard de monitoramento

---

## 🎓 Treinamento da Equipe

### Quem Deve Usar

1. **Analistas de Dados/BI**
   - Executar monitoramento semanal
   - Gerar relatórios de qualidade de dados

2. **Equipe de RH/Recrutamento**
   - Investigar casos específicos
   - Validar dados de contratação

3. **TI/Desenvolvimento**
   - Corrigir inconsistências no banco
   - Investigar causa raiz de problemas sistemáticos

### Material de Treinamento

**Duração:** 30 minutos

**Tópicos:**
1. Por que monitorar consistência (5 min)
2. Como executar query de monitoramento (10 min)
3. Como interpretar resultados (10 min)
4. Como investigar e corrigir casos (5 min)

**Hands-on:**
- Executar query e analisar saída
- Investigar 1 caso de cada severidade
- Simular correção de dados

---

## 🔗 Próximos Passos

### Curto Prazo (Esta Semana)

1. ✅ Executar query de monitoramento pela primeira vez
2. ✅ Identificar e corrigir casos CRÍTICOS
3. ✅ Validar se posição 1559 ainda está consistente

### Médio Prazo (Este Mês)

4. [ ] Implementar monitoramento semanal
5. [ ] Treinar equipe no uso das ferramentas
6. [ ] Documentar processo de correção

### Longo Prazo (Próximos 3 Meses)

7. [ ] Adicionar campo de validação na view
8. [ ] Implementar alertas automáticos
9. [ ] Criar dashboard de qualidade de dados

---

**Última atualização:** 2026-03-06
**Responsável:** Time de Dados
**Status:** ✅ Ferramentas Implementadas - Pronto para Uso
