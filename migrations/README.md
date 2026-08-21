# Migrations SQL

Migrations do banco de dados PostgreSQL para o projeto Inhire.

## 📁 Estrutura

### Migrations Ativas (060-084)
32 migrations aplicadas e ativas no banco.

**Últimas migrations:**
- `084_fix_candidaturas_remove_cliente_filter.sql` - View final de candidaturas
- `081_add_phone_candidaturas_view.sql` - Adiciona telefone do talento
- `080_update_candidaturas_filter_framework_billable.sql` - Filtros de workflow
- `079_decode_html_entities.sql` - Decode de entidades HTML

### `/applied_2024-2025`
59 migrations antigas já aplicadas (001-059).

**Conteúdo:**
- Migrations históricas do projeto
- Criação inicial das tabelas
- Índices e constraints básicos
- Views e functions iniciais

### `/obsolete_iterations`
20 migrations obsoletas/iterativas arquivadas.

**Tipos:**
- `*_STEP1_DROP.sql` / `*_STEP2_CREATE.sql` - Iterações de correção
- `*_FIXED.sql` - Versões corrigidas
- `*_debug.sql` - Versões de debug
- Migrations experimentais descartadas

---

## 📝 Convenções de Nomenclatura

```
XXX_descricao_da_migration.sql

Onde:
- XXX = Número sequencial (001, 002, ..., 084)
- descricao = snake_case descrevendo a mudança
```

**Exemplos:**
- `060_create_motivo_status_traducao.sql`
- `081_add_phone_candidaturas_view.sql`
- `084_fix_candidaturas_remove_cliente_filter.sql`

---

## 🔧 Como Aplicar Migrations

### Método 1: Script Python (Recomendado)

```bash
# Da raiz do projeto
python scripts/migration/run_migrations_direct.py
```

### Método 2: psql Direto

```bash
# Aplicar migration específica
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f migrations/084_fix_candidaturas_remove_cliente_filter.sql

# Aplicar todas as migrations pendentes
for file in migrations/0*.sql; do
    psql -U postgres -d inhire -f "$file"
done
```

---

## 📋 Checklist para Nova Migration

1. **Numeração:**
   - Verificar último número usado
   - Incrementar sequencialmente (ex: 084 → 085)

2. **Nomenclatura:**
   - Usar snake_case
   - Ser descritivo e conciso
   - Incluir tipo de operação (create, update, fix, add, remove)

3. **Conteúdo:**
   - Adicionar comentário no topo explicando a mudança
   - Usar `IF EXISTS` / `IF NOT EXISTS` quando apropriado
   - Incluir rollback se possível
   - Testar antes de aplicar em produção

4. **Documentação:**
   - Atualizar este README se necessário
   - Documentar em `docs/CLAUDE.md` se for mudança significativa

---

## ⚠️ Atenção

- **NÃO deletar migrations antigas** - podem ser necessárias para rollback
- **NÃO modificar migrations já aplicadas** - criar nova migration para correções
- **SEMPRE fazer backup** antes de aplicar migrations em produção
- **Testar em desenvolvimento** primeiro

---

## 🗂️ Organização

**Migrations ativas:** Raiz de `migrations/`
**Migrations antigas:** `applied_2024-2025/`
**Migrations obsoletas:** `obsolete_iterations/`

Esta estrutura mantém o histórico completo enquanto facilita localização das migrations relevantes.

---

**Última atualização:** 2026-08-21
**Total de migrations:** 111 (32 ativas + 59 aplicadas + 20 obsoletas)
