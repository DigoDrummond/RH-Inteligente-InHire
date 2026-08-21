# Changelog - 2026-02-03: Criação de Views de Análise

## Resumo da Sessão

Criadas duas views SQL consolidadas para facilitar análises de dados de posições e contratações no sistema InHire.

---

## 🎯 Objetivos Alcançados

### 1. View de Posições Fechadas ✅
- Criada view `vw_posicoes_fechadas`
- Consolidação de dados de contratações
- **664 registros** disponíveis

### 2. View de Análise de Posições ✅
- Criada view `vw_analise_posicoes`
- Análise completa com métricas calculadas
- **1.385 registros** disponíveis

---

## 📁 Arquivos Criados

### Migrations SQL
1. **`migrations/018_create_view_posicoes_fechadas.sql`**
   - View de posições fechadas/preenchidas
   - Inclui dados dos contratados
   - Calcula tempo de preenchimento

2. **`migrations/019_create_view_analise_posicoes.sql`**
   - View de análise abrangente
   - Métricas de SLA e prazos
   - Integração com funil de candidatos

### Scripts Python
1. **`create_view_posicoes_fechadas.py`**
   - Script para criar view de posições fechadas
   - Inclui validação e testes

2. **`create_view_analise_posicoes.py`**
   - Script para criar view de análise
   - Mostra exemplos de dados

3. **`test_view.py`**
   - Script de teste para view de posições fechadas
   - Validação de dados

### Documentação
1. **`docs/VIEWS_ANALISE_POSICOES.md`**
   - Documentação completa das views
   - Exemplos de consultas SQL
   - Guia de uso e troubleshooting

2. **`docs/changelogs/CHANGELOG_2026-02-03_VIEWS_ANALISE.md`** (este arquivo)
   - Resumo da sessão
   - Referência rápida

---

## 🔍 Detalhes Técnicos

### View 1: vw_posicoes_fechadas

**Propósito:** Listar contratações realizadas com detalhes dos contratados

**Campos Principais:**
- `codigo_posicao` - ID da posição
- `data_fechamento` - Data da contratação
- `status_fechado` - Status final
- `nome_contratado` - Nome do talento
- `email_contratado` - E-mail do talento
- `dias_para_preencher` - Tempo até contratação

**Filtros:**
- Status: `filled`, `hired`, `closed`
- Apenas com `hired_at` preenchido

**Exemplo de Uso:**
```sql
SELECT
    codigo_posicao,
    nome_vaga,
    nome_contratado,
    data_fechamento,
    dias_para_preencher
FROM vw_posicoes_fechadas
WHERE data_fechamento >= '2026-01-01'
ORDER BY data_fechamento DESC;
```

### View 2: vw_analise_posicoes

**Propósito:** Análise abrangente de posições com métricas de SLA e funil

**Campos Principais:**
- `codigo_posicao` - ID da posição
- `cargo` - Nome do cargo
- `cliente` - Nome do cliente
- `data_abertura` - Data de abertura
- `data_publicacao` - Data de publicação
- `status_atual` - Status atual
- `prazo_processo_seletivo` - SLA em dias
- `dias_em_aberto` - Dias desde abertura
- `indicador_prazo` - "Dentro do Prazo" / "Fora do Prazo"
- `etapa_funil` - Última etapa do funil

**Métricas Calculadas:**
1. **Dias em Aberto:** Diferença entre data atual (ou fechamento) e abertura
2. **Indicador de Prazo:** Compara dias em aberto com SLA configurado

**CTEs (Common Table Expressions):**
1. `ultima_etapa` - Identifica última etapa do funil por vaga
2. `ultimo_status` - Identifica último status por posição

**Exemplo de Uso:**
```sql
-- Posições fora do prazo
SELECT
    codigo_posicao,
    cargo,
    cliente,
    dias_em_aberto,
    prazo_processo_seletivo
FROM vw_analise_posicoes
WHERE indicador_prazo = 'Fora do Prazo'
AND status_atual = 'open'
ORDER BY dias_em_aberto DESC;
```

---

## 🚀 Como Utilizar

### Executar as Migrations

**Opção 1 - Via PostgreSQL:**
```bash
cd "G:\Meu Drive\Framework_Data\Inhire"

psql -U postgres -d inhire -f migrations/018_create_view_posicoes_fechadas.sql
psql -U postgres -d inhire -f migrations/019_create_view_analise_posicoes.sql
```

**Opção 2 - Via Python:**
```bash
cd "G:\Meu Drive\Framework_Data\Inhire"

python create_view_posicoes_fechadas.py
python create_view_analise_posicoes.py
```

### Testar as Views

```bash
# Testar view de posições fechadas
python test_view.py

# Consultar via psql
psql -U postgres -d inhire -c "SELECT COUNT(*) FROM vw_posicoes_fechadas;"
psql -U postgres -d inhire -c "SELECT COUNT(*) FROM vw_analise_posicoes;"
```

---

## 📊 Estatísticas Atuais

### vw_posicoes_fechadas
- **Total de registros:** 664
- **Período:** Todas as contratações históricas
- **Última atualização:** 2026-01-30

**Exemplo de Registro:**
```
Codigo: ae20d7bf-4010-4b42-b49a-16b5e0baeeaf
Data: 2026-01-30
Status: closed
Contratado: Giovanna Pires
Email: piresgiovanna02@hotmail.com
Vaga: Desenvolvedor(a) Python - Pleno
```

### vw_analise_posicoes
- **Total de registros:** 1.385
- **Posições abertas:** ~350 (estimativa)
- **Última atualização:** 2026-02-03

**Exemplo de Registro:**
```
Codigo: 485e3ab0-3eb9-416e-994f-f3dabc328738
Cargo: Estágio em Comunicação Interna
Data Abertura: 2026-01-29
Status: open
Dias em Aberto: 4
Prazo: Dentro do Prazo
Cliente: Framework
```

---

## 📈 Análises Sugeridas

### Análises Imediatas
1. **Time to Hire por Área**
   ```sql
   SELECT
       area_vaga,
       AVG(dias_para_preencher) as media_dias,
       COUNT(*) as total_contratacoes
   FROM vw_posicoes_fechadas
   WHERE dias_para_preencher IS NOT NULL
   GROUP BY area_vaga
   ORDER BY media_dias;
   ```

2. **SLA por Cliente**
   ```sql
   SELECT
       cliente,
       COUNT(*) as total,
       SUM(CASE WHEN indicador_prazo = 'Dentro do Prazo' THEN 1 ELSE 0 END) as dentro,
       SUM(CASE WHEN indicador_prazo = 'Fora do Prazo' THEN 1 ELSE 0 END) as fora,
       ROUND(AVG(dias_em_aberto), 2) as media_dias
   FROM vw_analise_posicoes
   WHERE indicador_prazo IS NOT NULL
   GROUP BY cliente
   ORDER BY total DESC;
   ```

3. **Distribuição por Status**
   ```sql
   SELECT
       status_atual,
       COUNT(*) as total,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentual
   FROM vw_analise_posicoes
   GROUP BY status_atual
   ORDER BY total DESC;
   ```

### Dashboards Recomendados
1. **Dashboard de Contratações**
   - Contratações por mês
   - Time to hire por área
   - Top cargos contratados

2. **Dashboard de SLA**
   - Posições dentro/fora do prazo
   - SLA por cliente
   - Tendência temporal

3. **Dashboard de Funil**
   - Posições por etapa
   - Taxa de conversão
   - Tempo médio por etapa

---

## 🔧 Problemas Encontrados e Soluções

### Problema 1: Conflito de Nome de Coluna
**Erro:** `coluna "event_metadata" não existe`

**Causa:** No modelo SQLAlchemy, a coluna está mapeada como `event_metadata` mas o nome real no banco é `metadata`.

**Solução:** Ajustada a query para usar o nome correto `metadata` na CTE `ultimo_status`.

**Arquivo:** `migrations/019_create_view_analise_posicoes.sql:24`

### Problema 2: Encoding de Caracteres Unicode
**Erro:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'`

**Causa:** Símbolos Unicode (✓) não são suportados pelo console Windows em cp1252.

**Solução:** Removidos caracteres Unicode especiais dos scripts Python, mantendo apenas ASCII.

**Arquivos:** `create_view_posicoes_fechadas.py`, `create_view_analise_posicoes.py`

---

## 🎯 Próximos Passos Recomendados

### Curto Prazo (Esta Semana)
- [ ] Criar dashboard no Metabase/PowerBI com as views
- [ ] Validar dados com stakeholders
- [ ] Documentar casos de uso específicos
- [ ] Criar alertas para posições fora do prazo

### Médio Prazo (Próximas 2 Semanas)
- [ ] Converter para materialized views (performance)
- [ ] Criar índices otimizados
- [ ] Implementar refresh automático
- [ ] Adicionar mais métricas calculadas

### Longo Prazo (Próximo Mês)
- [ ] Criar API REST para acesso aos dados
- [ ] Integrar com sistema de notificações
- [ ] Desenvolver relatórios automatizados
- [ ] Implementar análise preditiva (ML)

---

## 📚 Documentação Relacionada

### Documentos de Referência
- **`docs/VIEWS_ANALISE_POSICOES.md`** - Documentação completa das views
- **`docs/PROJECT_STRUCTURE.md`** - Estrutura do projeto
- **`docs/FLUXO_SINCRONIZACAO.md`** - Fluxo de sincronização de dados
- **`models/database.py`** - Schema do banco de dados

### Migrations Anteriores
- **`migrations/013_create_position_timeline_FIXED.sql`** - Tabela position_timeline
- **`migrations/016_create_custom_fields_table.sql`** - Campos customizados
- **`migrations/017_add_custom_fields_to_vagas.sql`** - Custom fields em vagas

---

## 🔗 Links Úteis

### Comandos Rápidos
```bash
# Ver estrutura das views
psql -U postgres -d inhire -c "\d+ vw_posicoes_fechadas"
psql -U postgres -d inhire -c "\d+ vw_analise_posicoes"

# Recriar as views (se necessário)
python create_view_posicoes_fechadas.py
python create_view_analise_posicoes.py

# Exportar dados para CSV
psql -U postgres -d inhire -c "COPY (SELECT * FROM vw_posicoes_fechadas) TO 'posicoes_fechadas.csv' CSV HEADER;"
```

### Queries de Validação
```sql
-- Verificar consistência de dados
SELECT
    'vw_posicoes_fechadas' as view_name,
    COUNT(*) as total,
    COUNT(DISTINCT codigo_posicao) as distinct_posicoes,
    MIN(data_fechamento) as primeira_contratacao,
    MAX(data_fechamento) as ultima_contratacao
FROM vw_posicoes_fechadas
UNION ALL
SELECT
    'vw_analise_posicoes',
    COUNT(*),
    COUNT(DISTINCT codigo_posicao),
    MIN(data_publicacao),
    MAX(data_publicacao)
FROM vw_analise_posicoes;
```

---

## 👥 Equipe

**Desenvolvedor:** Claude Code
**Data:** 2026-02-03
**Versão:** 1.0

---

## ✅ Checklist de Entrega

- [x] Views criadas no banco de dados
- [x] Scripts de criação testados
- [x] Documentação completa gerada
- [x] Exemplos de queries documentados
- [x] Changelog atualizado
- [x] Testes de validação executados
- [ ] Review com stakeholders
- [ ] Integração com BI tools
- [ ] Treinamento da equipe

---

## 📝 Notas Finais

As views estão prontas para uso e podem ser integradas imediatamente com ferramentas de BI ou usadas diretamente via SQL. Todos os arquivos foram criados e testados com sucesso.

Para continuar o trabalho, recomenda-se:
1. Revisar a documentação completa em `docs/VIEWS_ANALISE_POSICOES.md`
2. Executar as queries de exemplo para familiarização
3. Identificar necessidades específicas de análise
4. Criar dashboards conforme prioridades do negócio

**Arquivos principais para retomar:**
- `docs/VIEWS_ANALISE_POSICOES.md` - Documentação completa
- `migrations/018_create_view_posicoes_fechadas.sql` - View de contratações
- `migrations/019_create_view_analise_posicoes.sql` - View de análise

---

**Fim do Changelog - 2026-02-03**
