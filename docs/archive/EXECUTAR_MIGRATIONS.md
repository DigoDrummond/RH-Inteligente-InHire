# 🚀 Guia: Como Executar as Migrations

**IMPORTANTE:** Execute este guia para aplicar as melhorias estruturais no banco de dados.

---

## ⚡ Método Rápido (Recomendado)

### Opção 1: Via PowerShell (Mais Simples)

Abra o PowerShell e execute:

```powershell
cd "G:\Meu Drive\Framework_Data\Inhire\migrations"

# Migration 001 - Campos Calculados
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f "001_add_calculated_fields.sql"

# Migration 002 - Views Materializadas
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f "002_create_materialized_views.sql"

# Migration 003 - Tabela de Métricas
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f "003_create_metrics_table.sql"
```

---

### Opção 2: Via pgAdmin (Interface Gráfica)

1. Abra o pgAdmin 4
2. Conecte ao servidor PostgreSQL (localhost)
3. Selecione o banco de dados **inhire**
4. Clique em **Tools** → **Query Tool**
5. Para cada migration:
   - Clique em **Open File** (ícone de pasta)
   - Navegue até `G:\Meu Drive\Framework_Data\Inhire\migrations`
   - Abra o arquivo `001_add_calculated_fields.sql`
   - Clique em **Execute** (F5)
   - Repita para `002_create_materialized_views.sql`
   - Repita para `003_create_metrics_table.sql`

---

### Opção 3: Via Prompt de Comando (cmd)

Abra o Prompt de Comando e execute:

```cmd
cd /d "G:\Meu Drive\Framework_Data\Inhire\migrations"

"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f "001_add_calculated_fields.sql"

"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f "002_create_materialized_views.sql"

"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f "003_create_metrics_table.sql"
```

---

## ✅ Verificação

Após executar, verifique se foi bem-sucedido:

```sql
-- Verificar se campos calculados foram criados
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'candidaturas'
  AND column_name IN ('dias_no_processo', 'dias_no_stage_atual', 'created_at_inhire');

-- Deve retornar 3 linhas

-- Verificar se views materializadas foram criadas
SELECT matviewname
FROM pg_matviews
WHERE schemaname = 'public';

-- Deve retornar 4 views:
-- mv_funil_conversao
-- mv_kanban_dashboard
-- mv_sla_metrics
-- mv_candidaturas_summary

-- Verificar se tabela de métricas foi criada
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'candidatura_metrics';

-- Deve retornar 1 linha
```

---

## 🎯 Após Executar as Migrations

### 1. Atualizar Views Materializadas

```sql
SELECT refresh_all_materialized_views();
```

### 2. Testar Relatórios

```bash
# Dashboard completo
python relatorios/dashboard_consolidado.py

# Funil de conversão
python relatorios/funil_candidaturas.py

# Análise de SLA
python relatorios/analise_sla.py

# Taxas de conversão
python relatorios/taxas_conversao.py

# Exportar para Excel
python relatorios/export_excel.py
```

### 3. Verificar Dados

```sql
-- Ver funil de conversão
SELECT * FROM mv_funil_conversao ORDER BY stage_order;

-- Ver candidaturas atrasadas
SELECT vaga_name, talent_name, dias_atraso_sla
FROM mv_sla_metrics
WHERE status_sla = 'ATRASADO'
ORDER BY dias_atraso_sla DESC
LIMIT 10;

-- Ver resumo por vaga
SELECT vaga_name, total_candidaturas, taxa_contratacao_pct
FROM mv_candidaturas_summary
WHERE contratadas > 0
ORDER BY taxa_contratacao_pct DESC
LIMIT 10;
```

---

## 🔧 Troubleshooting

### Erro: "password authentication failed"
- Verifique a senha do usuário postgres
- Pode precisar configurar arquivo `.pgpass`

### Erro: "permission denied"
- Execute como administrador
- Verifique permissões no PostgreSQL

### Erro: "database does not exist"
- Verifique se está conectado ao banco "inhire"
- Liste bancos: `psql -U postgres -l`

### Erro: "column already exists"
- A migration já foi aplicada
- Pode pular para a próxima

---

## 📝 Ordem de Execução

**IMPORTANTE:** Execute na ordem exata:

1. `001_add_calculated_fields.sql` - Adiciona campos calculados
2. `002_create_materialized_views.sql` - Cria views (depende de #1)
3. `003_create_metrics_table.sql` - Cria tabela de métricas (depende de #1)

---

## 🆘 Em Caso de Problemas

Se encontrar problemas:

1. Verifique os logs do PostgreSQL:
   - Windows: `C:\Program Files\PostgreSQL\18\data\log\`

2. Execute cada migration separadamente e anote erros

3. Consulte a documentação completa:
   - `docs/MELHORIAS_ESTRUTURAIS.md`
   - `docs/RESUMO_IMPLEMENTACAO.md`

4. Verifique conexões ativas:
   ```sql
   SELECT * FROM pg_stat_activity WHERE datname = 'inhire';
   ```

---

## ✅ Status Final

Após executar todas as migrations com sucesso, você terá:

- ✅ 3 novos campos em `candidaturas`
- ✅ 2 triggers automáticos
- ✅ 4 views materializadas
- ✅ 1 tabela de métricas (`candidatura_metrics`)
- ✅ 3 funções PostgreSQL
- ✅ 8+ índices otimizados

**Tempo estimado:** 2-5 minutos

---

**Próximo passo:** Executar os relatórios Python para visualizar os resultados!

