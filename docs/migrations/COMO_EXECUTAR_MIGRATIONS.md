# Como Executar as Migrations 010 e 011

Existem 3 métodos para executar as migrations. Escolha o mais fácil para você:

---

## Método 1: Script Python (RECOMENDADO)

### Passo 1: Execute o script
```bash
python "G:\Meu Drive\Framework_Data\Inhire\apply_migrations.py"
```

### Passo 2: Digite a senha do PostgreSQL quando solicitado

O script vai:
- ✅ Conectar ao banco `inhire`
- ✅ Executar migration 010 (composite indexes)
- ✅ Executar migration 011 (check constraints)
- ✅ Mostrar os índices e constraints criados
- ✅ Exibir resumo final

---

## Método 2: pgAdmin (Interface Gráfica)

### Passo 1: Abra o pgAdmin 4

### Passo 2: Conecte ao servidor PostgreSQL
- Servers → PostgreSQL 18 → Databases → **inhire**

### Passo 3: Abra o Query Tool
- Clique com botão direito em **inhire**
- Selecione **Query Tool**

### Passo 4: Execute Migration 010
1. Abra o arquivo: `G:\Meu Drive\Framework_Data\Inhire\migrations\010_add_composite_index_candidatura.sql`
2. Copie todo o conteúdo
3. Cole no Query Tool
4. Clique em **Execute (F5)**
5. Aguarde mensagem de sucesso (deve aparecer "4 novos índices criados")

### Passo 5: Execute Migration 011
1. Abra o arquivo: `G:\Meu Drive\Framework_Data\Inhire\migrations\011_add_check_constraints.sql`
2. Copie todo o conteúdo
3. Cole no Query Tool
4. Clique em **Execute (F5)**
5. Aguarde mensagem de sucesso (deve aparecer "check constraints criadas")

---

## Método 3: Linha de Comando (psql)

### Via CMD (Prompt de Comando)

Abra o **CMD** e execute:

```cmd
cd "C:\Program Files\PostgreSQL\18\bin"

REM Executar Migration 010
psql -U postgres -d inhire -f "G:\Meu Drive\Framework_Data\Inhire\migrations\010_add_composite_index_candidatura.sql"

REM Executar Migration 011
psql -U postgres -d inhire -f "G:\Meu Drive\Framework_Data\Inhire\migrations\011_add_check_constraints.sql"
```

Digite a senha do PostgreSQL quando solicitado.

---

## Verificar se as Migrations Foram Aplicadas

### Via Python:
```bash
python -c "import psycopg2; conn = psycopg2.connect('dbname=inhire user=postgres'); cur = conn.cursor(); cur.execute(\"SELECT COUNT(*) FROM pg_indexes WHERE tablename='candidaturas' AND indexname LIKE 'idx_candidatura%'\"); print(f'Indices criados: {cur.fetchone()[0]}'); cur.execute(\"SELECT COUNT(*) FROM pg_constraint WHERE conname LIKE 'chk_%'\"); print(f'Check constraints criadas: {cur.fetchone()[0]}')"
```

### Via psql:
```sql
-- Verificar índices
SELECT indexname
FROM pg_indexes
WHERE tablename = 'candidaturas'
  AND indexname LIKE 'idx_candidatura%'
ORDER BY indexname;

-- Verificar check constraints
SELECT conname, conrelid::regclass as table_name
FROM pg_constraint
WHERE conname LIKE 'chk_%'
ORDER BY conrelid::regclass::text, conname;
```

**Resultado Esperado:**
- **4 índices** criados em `candidaturas`:
  - `idx_candidatura_status_updated`
  - `idx_candidatura_vaga`
  - `idx_candidatura_talento`
  - `idx_candidatura_source`

- **Múltiplas check constraints** criadas em várias tabelas:
  - `chk_talento_email_format` (talentos)
  - `chk_vaga_status_valid` (vagas)
  - `chk_candidatura_dates_logical` (candidaturas)
  - E outras...

---

## Troubleshooting

### Erro: "password authentication failed"
**Solução:** Certifique-se de usar a senha correta do usuário `postgres`

### Erro: "relation already exists"
**Solução:** A migration já foi aplicada. Você pode ignorar este erro com segurança.

### Erro: "database inhire does not exist"
**Solução:** O banco `inhire` não existe. Crie-o primeiro:
```sql
CREATE DATABASE inhire;
```

### Timeout ao executar
**Solução:** As migrations podem demorar se houver muitos dados. Isso é normal. Aguarde até 2 minutos.

---

## O que cada Migration faz?

### Migration 010: Composite Indexes
Cria 4 índices otimizados para queries comuns:
- **Índice composto** (status, updated_at_inhire) - Para sync incremental
- **Índice por vaga** (vaga_id, status) - Para listar candidaturas de uma vaga
- **Índice por talento** (talento_id) - Para buscar candidaturas de um talento
- **Índice por source** (source) - Para análise de origem de candidaturas

**Impacto:** Queries 5-10x mais rápidas em tabelas grandes

### Migration 011: Check Constraints
Adiciona validações no banco de dados:
- **Email válido** em talentos (formato @ .dominio)
- **Status válido** em vagas (open, closed, draft, etc)
- **Datas lógicas** em candidaturas (updated_at >= created_at)
- **Consistência hired/filled** em posições
- **Valores positivos** em campos numéricos

**Impacto:** Previne dados inválidos no banco, aumenta confiabilidade

---

## Suporte

Se tiver problemas, verifique:
1. PostgreSQL está rodando?
2. Senha está correta?
3. Banco `inhire` existe?
4. Usuário `postgres` tem permissões?

Para mais ajuda, abra um issue no repositório.
