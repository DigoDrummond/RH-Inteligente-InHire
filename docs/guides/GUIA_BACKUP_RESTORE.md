# Guia Completo de Backup e Restauração - Banco de Dados Inhire

**Data:** 2026-03-23
**Versão:** 2.0 - Com Compressão GZIP
**Status:** ✅ Implementado e Testado

---

## 📋 Sumário

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Estrutura de Arquivos](#estrutura-de-arquivos)
4. [Realizando Backup](#realizando-backup)
5. [Restaurando Backup](#restaurando-backup)
6. [Validação](#validação)
7. [Agendamento Automático](#agendamento-automático)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## 🎯 Visão Geral

Sistema completo de backup e restauração para o banco de dados PostgreSQL da aplicação Inhire.

### Características

- ✅ **Backup completo** de todas as tabelas, views, funções e dados
- ✅ **4 formatos de backup** para máxima compatibilidade
- ✅ **Compressão GZIP automática** - economia de 70-80% em arquivos SQL
- ✅ **Validações automáticas** antes e depois do backup
- ✅ **Logs detalhados** de todas as operações
- ✅ **Restauração fácil** com menu interativo
- ✅ **Backup data-only** para restauração seletiva
- ✅ **Segurança** - não expõe credenciais

### O Que É Incluído no Backup

**Tabelas (17):**
- vagas, posicoes, position_timeline
- candidaturas, candidatura_timeline
- talentos, talento_arquivos, talento_tags
- requisicoes, vaga_tags
- clientes, custom_fields
- sync_configuration, sync_log
- feriados

**Views (~6):**
- vw_analise_posicoes
- vw_funil_performance
- vw_dados_jade
- vw_analise_requisicoes
- vw_performance_por_estagio
- vw_transicoes_estagio

**Funções Críticas:**
- calcular_dias_uteis()
- update_updated_at_column()
- update_position_timeline_updated_at()

**Estrutura:**
- Enums (vagastatusenum, candidaturastatusenum, etc.)
- Índices
- Constraints (PK, FK, CHECK)
- Sequences
- Triggers

---

## 🔧 Pré-requisitos

### Software Necessário

1. **PostgreSQL 18** instalado em:
   ```
   C:\Program Files\PostgreSQL\18\bin\
   ```

2. **Permissões de acesso:**
   - Usuário: `postgres`
   - Database: `inhire`
   - Credenciais configuradas no arquivo `.env`

3. **Espaço em disco:**
   - Mínimo: 500 MB livres
   - Recomendado: 2 GB livres

### Verificar Instalação

```bash
# Testar se PostgreSQL está acessível
"C:\Program Files\PostgreSQL\18\bin\psql.exe" --version

# Testar conexão
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "SELECT version();"
```

---

## 📁 Estrutura de Arquivos

### Diretório de Backups

```
Backup_BD_Inhire/
├── full/                   # Backups custom format (.dump)
│   ├── inhire_backup_2026-03-23_14-30-00.dump
│   └── inhire_backup_2026-03-22_08-00-00.dump
│
├── sql/                    # Backups SQL plain text
│   ├── inhire_backup_2026-03-23_14-30-00.sql.gz    # ✅ Comprimido (70-80% menor)
│   ├── inhire_backup_2026-03-23_14-30-00.sql       # Original (opcional)
│   └── inhire_backup_2026-03-22_08-00-00.sql.gz
│
├── schema/                 # Schema-only backups
│   ├── inhire_schema_20260323.sql.gz               # ✅ Comprimido (80% menor)
│   ├── inhire_schema_20260323.sql                  # Original (opcional)
│   └── inhire_schema_20260322.sql.gz
│
├── data/                   # Data-only backups (NOVO)
│   ├── inhire_data_2026-03-23_14-30-00.dump
│   └── inhire_data_2026-03-22_08-00-00.dump
│
├── restore_scripts/        # Scripts de restauração específicos (NOVO)
│   └── restore_from_sql_gz.bat
│
├── logs/                   # Logs de execução
│   ├── backup_2026-03-23_14-30-00.log
│   └── backup_2026-03-22_08-00-00.log
│
└── latest/                 # Último backup (link)
    └── inhire_latest.dump
```

### Scripts Disponíveis

```
scripts/backup/
├── backup_inhire_windows.bat      # Script principal de backup (com compressão)
├── restore_inhire_windows.bat     # Script de restauração (multi-formato)
├── compress_backups.bat           # Utilitário de compressão manual
└── validate_backup.sql            # Validações SQL

Backup_BD_Inhire/restore_scripts/
└── restore_from_sql_gz.bat        # Restauração específica de .sql.gz
```

---

## 💾 Realizando Backup

### ⚠️ Requisito: GZIP

O sistema de backup requer `gzip` para compressão automática de arquivos SQL.

**Verificar se gzip está disponível:**
```cmd
where gzip
```

**Se não encontrado:**
- Instalar Git for Windows: https://git-scm.com/download/win
- Ou instalar gzip standalone

**Nota:** Custom format (.dump) já vem com compressão interna do PostgreSQL.

### Backup Manual (Método Recomendado)

#### Passo 1: Navegar para o diretório

```cmd
cd C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire
cd scripts\backup
```

#### Passo 2: Executar script de backup

```cmd
backup_inhire_windows.bat
```

#### Passo 3: Aguardar conclusão

O script irá:
1. ✅ Validar pré-requisitos
2. ✅ Testar conexão com banco
3. ✅ Criar backup custom format (.dump)
4. ✅ Criar backup SQL plain text (.sql)
5. ✅ **Comprimir SQL para .sql.gz** (economia 70-80%)
6. ✅ Criar backup schema-only (.sql)
7. ✅ **Comprimir schema para .sql.gz** (economia 80%)
8. ✅ Criar backup data-only (.dump)
9. ✅ Gerar log detalhado
10. ✅ Atualizar link para "latest"

**Tempo estimado:** 3-7 minutos (dependendo do tamanho do banco)

### Saída Esperada

```
============================================================================
BACKUP COMPLETO DO BANCO DE DADOS INHIRE
============================================================================

Data/Hora: 2026-03-23_14-30-00
Database: inhire
Host: localhost:5432
Usuario: postgres

Destino: C:\...\Backup_BD_Inhire

============================================================================

[INFO] Validando pre-requisitos...
[OK] pg_dump.exe encontrado
[OK] Arquivo .env encontrado
[OK] Credenciais carregadas do .env
[OK] Diretorios criados/verificados
[OK] Conexao com banco de dados estabelecida

============================================================================
BACKUP 1/3: Custom Format (.dump) - FORMATO PRINCIPAL
============================================================================
[INFO] Iniciando backup custom format...
[INFO] Arquivo: ...\full\inhire_backup_2026-03-23_14-30-00.dump
[INFO] Formato: Custom (comprimido, restauravel)

[OK] Backup custom format concluido com sucesso
[OK] Tamanho: 45 MB (47185920 bytes)

============================================================================
BACKUP 2/3: SQL Plain Text (.sql) - FORMATO LEGIVEL
============================================================================
[INFO] Iniciando backup SQL plain text...
[OK] Backup SQL plain text concluido
[OK] Tamanho: 128 MB (134217728 bytes)

============================================================================
BACKUP 3/3: Schema Only (.sql) - APENAS ESTRUTURA
============================================================================
[INFO] Iniciando backup schema only...
[OK] Backup schema only concluido
[OK] Tamanho: 156 KB (159744 bytes)

[OK] Link para ultimo backup atualizado

============================================================================
RESUMO DO BACKUP
============================================================================

[OK] Backup concluido com sucesso!

Arquivos criados:
  1. Custom format:  ...\full\inhire_backup_2026-03-23_14-30-00.dump
     Tamanho: 45 MB

  2. SQL plain text: ...\sql\inhire_backup_2026-03-23_14-30-00.sql
     Tamanho: 128 MB

  3. Schema only:    ...\schema\inhire_schema_20260323.sql
     Tamanho: 156 KB

  Log detalhado:     ...\logs\backup_2026-03-23_14-30-00.log

============================================================================
```

### Formatos de Backup

| Formato | Extensão | Tamanho | Uso | Vantagens |
|---------|----------|---------|-----|-----------|
| **Custom** | .dump | ~29 MB | ✅ Restauração principal | Comprimido (gzip), seletivo, rápido |
| **SQL** | .sql | ~128 MB | Auditoria/edição | Legível, editável |
| **SQL.GZ** | .sql.gz | ~25-30 MB | ✅ Backup secundário | Comprimido (70-80%), legível após descomprimir |
| **Schema** | .sql | ~156 KB | Estrutura/versioning | Leve, versionável |
| **Schema.GZ** | .sql.gz | ~30 KB | Estrutura comprimida | Economia de 80% |
| **Data Only** | .dump | ~28 MB | Restauração de dados | Apenas dados, sem schema |

---

## 🔄 Restaurando Backup

### Restauração Manual

⚠️ **ATENÇÃO:** A restauração irá **SOBRESCREVER** todos os dados atuais do banco!

#### Passo 1: Navegar para o diretório

```cmd
cd C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire
cd scripts\backup
```

#### Passo 2: Executar script de restauração

```cmd
restore_inhire_windows.bat
```

#### Passo 3: Seguir o menu interativo

```
============================================================================
RESTAURACAO DO BANCO DE DADOS INHIRE
============================================================================

[AVISO] Este script ira SOBRESCREVER o banco de dados atual!

============================================================================
SELECIONE O TIPO DE RESTAURACAO
============================================================================

1. Restaurar do backup mais recente (latest)
2. Restaurar de arquivo custom format (.dump)
3. Restaurar de arquivo SQL plain text (.sql)
4. Listar backups disponiveis
5. Cancelar

Digite sua opcao (1-5):
```

#### Opções de Restauração

**Opção 1: Backup Mais Recente (Recomendado)**
- Usa o arquivo `latest/inhire_latest.dump`
- Mais rápido e simples

**Opção 2: Arquivo Custom (.dump)**
- Permite escolher um backup específico
- Lista todos os arquivos .dump disponíveis
- Restauração rápida e confiável

**Opção 3: Arquivo SQL (.sql)**
- Permite escolher um backup SQL específico
- Útil se o .dump estiver corrompido
- Mais lento que custom format

**Opção 4: Listar Backups**
- Mostra todos os backups disponíveis
- Não executa restauração

#### Passo 4: Confirmar operação

```
============================================================================
CONFIRMACAO FINAL
============================================================================

[AVISO CRITICO] Esta operacao ira:
  1. APAGAR todos os dados atuais do banco 'inhire'
  2. RESTAURAR os dados do backup selecionado
  3. Esta acao NAO PODE SER DESFEITA

Arquivo de backup: ...\full\inhire_backup_2026-03-23_14-30-00.dump
Tamanho: 45 MB

Tem certeza que deseja continuar? (S/N):
```

Digite `S` para confirmar ou `N` para cancelar.

#### Passo 5: Aguardar conclusão

O script irá:
1. ✅ Encerrar conexões ativas
2. ✅ Restaurar dados do backup
3. ✅ Validar restauração
4. ✅ Contar tabelas/views/funções
5. ✅ Contar registros principais

**Tempo estimado:** 3-10 minutos

### Saída Esperada

```
============================================================================
ETAPA 1/3: PREPARACAO DO BANCO
============================================================================

[INFO] Encerrando conexoes ativas...
[OK] Conexoes encerradas

============================================================================
ETAPA 2/3: RESTAURACAO DOS DADOS
============================================================================

[INFO] Restaurando do formato custom (.dump)...
[INFO] Isso pode levar alguns minutos...

[OK] Restauracao custom format concluida

============================================================================
ETAPA 3/3: VALIDACAO POS-RESTAURACAO
============================================================================

[INFO] Executando validacoes basicas...

[INFO] Tabelas encontradas: 17
[INFO] Views encontradas: 6
[INFO] Funcoes encontradas: 3

[INFO] Contando registros nas tabelas principais...

 tabela       | registros
--------------+-----------
 candidaturas |     85234
 posicoes     |      1383
 talentos     |     61916
 vagas        |       679

============================================================================
RESUMO DA RESTAURACAO
============================================================================

[OK] Restauracao concluida!

Estatisticas:
  - Tabelas: 17
  - Views: 6
  - Funcoes: 3

Arquivo restaurado: ...\full\inhire_backup_2026-03-23_14-30-00.dump
```

---

## ✅ Validação

### Validação Manual (Recomendado)

Após backup ou restauração, execute o script de validação:

```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f scripts\backup\validate_backup.sql
```

### O Que É Validado

O script `validate_backup.sql` executa 12 validações:

1. **Estrutura do Banco** - Conta tabelas, views, funções, sequences
2. **Tabelas Principais** - Verifica existência de 15 tabelas críticas
3. **Views Críticas** - Verifica 6 views principais
4. **Funções Críticas** - Verifica 3 funções essenciais
5. **Contagem de Registros** - Conta dados nas principais tabelas
6. **Integridade Referencial** - Verifica constraints de FK
7. **Índices** - Lista todos os índices criados
8. **Teste de Funções** - Executa `calcular_dias_uteis()`
9. **Teste de Views** - Consulta `vw_analise_posicoes`
10. **Dados Recentes** - Verifica últimos registros sincronizados
11. **Últimas Sincronizações** - Mostra log de sync
12. **Tamanho do Banco** - Calcula espaço em disco

### Valores Esperados

| Validação | Valor Esperado | Descrição |
|-----------|----------------|-----------|
| Tabelas | 17 | Tabelas do schema public |
| Views | 6+ | Views principais |
| Funções | 3+ | Funções críticas |
| Candidaturas | ~85.000 | Registros de candidaturas |
| Talentos | 61.000-86.000 | Talentos sincronizados |
| Posições | ~1.400 | Posições ativas e fechadas |
| Vagas | ~680 | Vagas abertas e fechadas |

### Validação Rápida (SQL Direto)

```sql
-- Contar objetos principais
SELECT
    'Tabelas' as tipo, COUNT(*) as qtd
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
UNION ALL
SELECT 'Views', COUNT(*)
FROM information_schema.views
WHERE table_schema = 'public'
UNION ALL
SELECT 'Funcoes', COUNT(*)
FROM information_schema.routines
WHERE table_schema = 'public';

-- Contar registros principais
SELECT 'vagas' as tabela, COUNT(*) FROM vagas
UNION ALL SELECT 'posicoes', COUNT(*) FROM posicoes
UNION ALL SELECT 'candidaturas', COUNT(*) FROM candidaturas
UNION ALL SELECT 'talentos', COUNT(*) FROM talentos;

-- Testar função crítica
SELECT calcular_dias_uteis('2024-01-01'::DATE, '2024-01-31'::DATE);

-- Testar view crítica
SELECT COUNT(*) FROM vw_analise_posicoes;
```

---

## 🕐 Agendamento Automático

### Estratégia Recomendada

| Tipo de Backup | Frequência | Horário | Retenção |
|----------------|------------|---------|----------|
| **Custom (.dump)** | Diário | 03:00 | 30 dias |
| **SQL (.sql)** | Semanal | Domingo 02:00 | 90 dias |
| **Schema (.sql)** | Semanal | Domingo 02:30 | 180 dias |

### Agendar no Windows Task Scheduler

#### Passo 1: Abrir Agendador de Tarefas

1. Pressionar `Win + R`
2. Digite `taskschd.msc`
3. Pressionar Enter

#### Passo 2: Criar Nova Tarefa

1. Clique em **"Criar Tarefa Básica"**
2. Nome: `Backup Diário - Banco Inhire`
3. Descrição: `Backup automático do banco de dados Inhire`

#### Passo 3: Configurar Gatilho

1. Escolha **"Diariamente"**
2. Horário: `03:00`
3. Repetir: A cada `1 dia`

#### Passo 4: Configurar Ação

1. Ação: **"Iniciar um programa"**
2. Programa/script:
   ```
   C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\scripts\backup\backup_inhire_windows.bat
   ```
3. Iniciar em:
   ```
   C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\scripts\backup
   ```

#### Passo 5: Configurações Adicionais

- ✅ Executar com privilégios mais altos
- ✅ Executar mesmo que o usuário não esteja conectado
- ✅ Não iniciar a tarefa se o computador estiver em bateria

### Script de Limpeza de Backups Antigos

Crie um script `cleanup_old_backups.bat`:

```batch
@echo off
REM Limpar backups com mais de 30 dias

set "BACKUP_ROOT=C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\Backup_BD_Inhire"

echo Limpando backups antigos (30+ dias)...

forfiles /p "%BACKUP_ROOT%\full" /s /m *.dump /d -30 /c "cmd /c del @path"
forfiles /p "%BACKUP_ROOT%\sql" /s /m *.sql /d -30 /c "cmd /c del @path"
forfiles /p "%BACKUP_ROOT%\logs" /s /m *.log /d -60 /c "cmd /c del @path"

echo Limpeza concluida!
pause
```

Agende para executar semanalmente após o backup.

---

## 🔧 Troubleshooting

### Problema: "pg_dump.exe não encontrado"

**Causa:** PostgreSQL não instalado ou caminho incorreto

**Solução:**
1. Verificar instalação:
   ```cmd
   dir "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
   ```
2. Se não existir, instalar PostgreSQL 18
3. Se estiver em outro caminho, editar script `backup_inhire_windows.bat`:
   ```batch
   set "PSQL_BIN=C:\SeuCaminho\PostgreSQL\18\bin"
   ```

### Problema: "DB_PASSWORD não encontrada no arquivo .env"

**Causa:** Arquivo `.env` sem credencial ou formato incorreto

**Solução:**
1. Verificar arquivo `.env` existe:
   ```cmd
   dir .env
   ```
2. Abrir `.env` e verificar linha:
   ```env
   DB_PASSWORD=SuaSenhaAqui
   ```
3. Formato correto (sem espaços, sem aspas):
   ```env
   DB_PASSWORD=postgres
   ```

### Problema: "Não foi possível conectar ao banco de dados"

**Causa:** PostgreSQL não está rodando ou credenciais incorretas

**Solução:**
1. Verificar se PostgreSQL está rodando:
   ```cmd
   sc query postgresql-x64-18
   ```
2. Se não estiver, iniciar serviço:
   ```cmd
   net start postgresql-x64-18
   ```
3. Testar conexão manual:
   ```cmd
   "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire
   ```

### Problema: "Arquivo de backup muito pequeno"

**Causa:** Backup falhou ou banco vazio

**Solução:**
1. Verificar log detalhado:
   ```cmd
   type Backup_BD_Inhire\logs\backup_*.log
   ```
2. Verificar se banco tem dados:
   ```sql
   SELECT COUNT(*) FROM vagas;
   ```
3. Executar backup novamente

### Problema: "Erro ao restaurar do SQL"

**Causa:** Arquivo SQL corrompido ou incompatível

**Solução:**
1. Usar backup custom format (.dump) em vez de SQL:
   ```cmd
   restore_inhire_windows.bat
   # Escolher opção 2 (custom format)
   ```
2. Se persistir, executar sync completa:
   ```cmd
   python run_sync.py --full
   ```

### Problema: "Espaço em disco insuficiente"

**Causa:** Disco cheio

**Solução:**
1. Verificar espaço disponível:
   ```cmd
   wmic logicaldisk get size,freespace,caption
   ```
2. Limpar backups antigos:
   ```cmd
   cleanup_old_backups.bat
   ```
3. Mover backups para outro disco:
   ```cmd
   move Backup_BD_Inhire D:\Backups\
   ```

---

## ❓ FAQ

### 1. Com que frequência devo fazer backup?

**Resposta:**
- **Diário:** Backup custom format às 03:00
- **Semanal:** Backup SQL completo aos domingos
- **Antes de alterações:** Sempre antes de migrations ou mudanças críticas

### 2. Quanto espaço em disco preciso?

**Resposta:**
- **Backup custom (.dump):** ~45-60 MB por backup
- **Backup SQL (.sql):** ~120-150 MB por backup
- **Recomendado:** 2 GB livres (para 30 dias de backups)

### 3. Posso executar backup com aplicação rodando?

**Resposta:**
Sim! O `pg_dump` faz backup sem travar o banco. Mas:
- ✅ Backup pode ser feito durante operação normal
- ⚠️ Evite durante sincronizações pesadas (sync completa)
- ✅ Melhor horário: Madrugada (03:00) quando há menos carga

### 4. Como restaurar apenas uma tabela específica?

**Resposta:**
Use `pg_restore` com opção `--table`:

```cmd
"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" ^
  -U postgres ^
  -d inhire ^
  --table=vagas ^
  --clean ^
  --if-exists ^
  Backup_BD_Inhire\full\inhire_backup_2026-03-23_14-30-00.dump
```

### 5. Backup inclui senhas e credenciais?

**Resposta:**
- ❌ **NÃO inclui:** Usuários, senhas, roles do PostgreSQL
- ✅ **Inclui:** Todos os dados das tabelas (incluindo campos como `api_key` se houver)
- ⚠️ **Segurança:** Mantenha backups em local seguro, criptografado

### 6. Posso usar backup de versão diferente do PostgreSQL?

**Resposta:**
- ✅ **Versões compatíveis:** PostgreSQL 15, 16, 17, 18
- ⚠️ **Versões antigas:** PostgreSQL 12, 13, 14 podem ter problemas
- ✅ **Recomendado:** Usar mesma versão major (18.x)

### 7. Como transferir backup para outro servidor?

**Resposta:**

**Método 1: Copiar arquivo e restaurar**
```cmd
# Servidor origem
copy Backup_BD_Inhire\full\inhire_latest.dump \\servidor-destino\c$\temp\

# Servidor destino
pg_restore -U postgres -d inhire_novo -h localhost C:\temp\inhire_latest.dump
```

**Método 2: Dump direto para servidor remoto**
```cmd
pg_dump -U postgres -h servidor-origem -d inhire | psql -U postgres -h servidor-destino -d inhire_novo
```

### 8. Backup inclui histórico de sincronizações?

**Resposta:**
Sim! A tabela `sync_log` é incluída com todo o histórico.

### 9. Como validar integridade do backup?

**Resposta:**

**Método 1: Validação automática (incluída no script)**
```cmd
backup_inhire_windows.bat
# Valida automaticamente após criar backup
```

**Método 2: Validação manual**
```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -f scripts\backup\validate_backup.sql
```

**Método 3: Listar conteúdo do backup**
```cmd
"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" --list Backup_BD_Inhire\full\inhire_latest.dump
```

### 10. Posso cancelar backup ou restauração no meio?

**Resposta:**

**Durante Backup:**
- ✅ Pode cancelar com `Ctrl+C`
- ✅ Arquivo parcial será criado (deve ser descartado)
- ✅ Banco não é afetado

**Durante Restauração:**
- ⚠️ Pode cancelar mas banco ficará em estado inconsistente
- ❌ **NÃO RECOMENDADO** - deixe terminar
- 🔄 Se cancelou, execute restauração novamente do zero

---

## 📞 Suporte

### Logs e Diagnóstico

**Ver último log de backup:**
```cmd
type Backup_BD_Inhire\logs\backup_*.log | more
```

**Ver últimas sincronizações:**
```sql
SELECT * FROM sync_log ORDER BY start_time DESC LIMIT 5;
```

**Ver tamanho atual do banco:**
```sql
SELECT pg_size_pretty(pg_database_size('inhire'));
```

### Recursos Adicionais

- **Documentação PostgreSQL:** https://www.postgresql.org/docs/18/backup.html
- **CLAUDE.md:** Documentação do projeto Inhire
- **Logs da aplicação:** `logs/inhire_sync.log`

---

## 📝 Changelog

**2026-03-23** - Versão 1.0
- ✅ Sistema de backup completo implementado
- ✅ Scripts Windows (.bat) criados
- ✅ Validações automáticas
- ✅ Documentação completa
- ✅ 3 formatos de backup
- ✅ Menu interativo de restauração

---

**Última atualização:** 2026-03-23
**Autor:** Auto-gerado
**Status:** ✅ Pronto para Produção
