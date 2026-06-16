# Guia de Backup e Recovery - InHire Sync

**Data de criação:** 16/01/2026
**Versão:** 1.0

---

## 📋 Visão Geral

Sistema completo de backup e recovery para o banco de dados PostgreSQL do InHire Sync.

### Estratégia 3-2-1

```
3 cópias dos dados:
  ├─ 1. Produção (PostgreSQL ativo)
  ├─ 2. Backup local (disco)
  └─ 3. Backup remoto (S3/Cloud - opcional)

2 tipos de mídia:
  ├─ Disco local (SSD/HDD)
  └─ Cloud storage (S3)

1 cópia offsite:
  └─ S3 (datacenter diferente)
```

---

## 🚀 Setup Inicial

### Windows

```powershell
# 1. Configurar variáveis de ambiente
$env:DB_PASSWORD = "sua_senha"
$env:SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK"

# 2. Executar backup manual para testar
cd "G:\Meu Drive\Framework_Data\Inhire\scripts\backup"
.\backup_database.ps1 -Mode full

# 3. Agendar no Task Scheduler (ver seção Agendamento)
```

### Linux

```bash
# 1. Tornar script executável
chmod +x scripts/backup/backup_database.sh

# 2. Configurar variáveis de ambiente
export DB_PASSWORD="sua_senha"
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK"
export S3_BUCKET="s3://framework-backups/inhire"
export S3_ENABLED="true"

# 3. Executar backup manual para testar
./scripts/backup/backup_database.sh full

# 4. Agendar no cron (ver seção Agendamento)
```

---

## 📦 Tipos de Backup

### 1. Full Backup (Semanal)

**Quando:** Domingos, 01:00
**Duração:** ~2-5 minutos
**Tamanho:** ~50-200 MB (comprimido)

```powershell
# Windows
.\backup_database.ps1 -Mode full

# Linux
./backup_database.sh full
```

**O que faz:**
- Dump completo do banco de dados
- Comprime com gzip/zip
- Envia para S3 (opcional)
- Remove backups > 30 dias
- Envia notificação Slack

### 2. Incremental Backup (Diário)

**Quando:** Segunda a Sábado, 02:00
**Duração:** ~1-3 minutos
**Tamanho:** ~20-100 MB (comprimido)

```powershell
# Windows
.\backup_database.ps1 -Mode incremental

# Linux
./backup_database.sh incremental
```

**O que faz:**
- Dump do banco atual
- Comprime
- Remove backups > 7 dias
- Notificação Slack

### 3. Teste de Restore (Mensal)

**Quando:** 1º dia do mês, 03:00
**Duração:** ~3-7 minutos

```powershell
# Windows
.\backup_database.ps1 -Mode test

# Linux
./backup_database.sh test
```

**O que faz:**
- Cria database temporário
- Restaura último backup full
- Verifica integridade (contagem de tabelas)
- Remove database temporário
- Notifica resultado

---

## ⏰ Agendamento

### Windows Task Scheduler

#### 1. Full Backup (Semanal)
```powershell
# Criar Task via PowerShell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"G:\Meu Drive\Framework_Data\Inhire\scripts\backup\backup_database.ps1`" -Mode full"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 1am

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "InHire Full Backup" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -User "SYSTEM" `
    -RunLevel Highest `
    -Description "Backup semanal completo do banco InHire"
```

#### 2. Incremental Backup (Diário)
```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"G:\Meu Drive\Framework_Data\Inhire\scripts\backup\backup_database.ps1`" -Mode incremental"

$trigger = New-ScheduledTaskTrigger -Daily -At 2am -DaysInterval 1

Register-ScheduledTask -TaskName "InHire Incremental Backup" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -User "SYSTEM" `
    -RunLevel Highest
```

#### 3. Teste Mensal
```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"G:\Meu Drive\Framework_Data\Inhire\scripts\backup\backup_database.ps1`" -Mode test"

$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At 3am

Register-ScheduledTask -TaskName "InHire Backup Test" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -User "SYSTEM" `
    -RunLevel Highest
```

### Linux Cron

```bash
# Editar crontab
crontab -e

# Adicionar linhas:
# Full backup: Domingos 01:00
0 1 * * 0  /path/to/backup_database.sh full >> /var/log/inhire_backup.log 2>&1

# Incremental backup: Segunda a Sábado 02:00
0 2 * * 1-6  /path/to/backup_database.sh incremental >> /var/log/inhire_backup.log 2>&1

# Teste de restore: 1º dia do mês 03:00
0 3 1 * *  /path/to/backup_database.sh test >> /var/log/inhire_backup.log 2>&1
```

---

## 🔄 Recovery (Restauração)

### Cenário 1: Restore de Backup Específico

```powershell
# Windows
.\backup_database.ps1 -Mode restore -BackupFile "G:\...\backups\full\inhire_full_20260116_010000.dump.zip"

# Linux
./backup_database.sh restore /backups/inhire/full/inhire_full_20260116_010000.dump.gz
```

### Cenário 2: Restore do Backup Mais Recente

```powershell
# Windows
$latest = "G:\Meu Drive\Framework_Data\Inhire\backups\full\inhire_full_latest.dump.zip"
.\backup_database.ps1 -Mode restore -BackupFile $latest

# Linux
./backup_database.sh restore /backups/inhire/full/inhire_full_latest.dump.gz
```

### Cenário 3: Restore de S3 (Cloud)

```bash
# 1. Download do S3
aws s3 cp s3://framework-backups/inhire/full/inhire_full_20260116.dump.gz /tmp/

# 2. Restore
./backup_database.sh restore /tmp/inhire_full_20260116.dump.gz
```

---

## 📊 RTO/RPO

### Recovery Time Objective (RTO)
**Tempo para restaurar sistema após desastre**

| Cenário | RTO | Passos |
|---------|-----|--------|
| Backup local | 10-15 min | 1. Identificar backup<br>2. Executar restore<br>3. Verificar integridade |
| Backup S3 | 20-30 min | 1. Download S3 (~5 min)<br>2. Restore local<br>3. Verificação |
| Sem backup | 4-8 horas | 1. Re-sync completo<br>2. Validação manual |

### Recovery Point Objective (RPO)
**Quanto de dados podemos perder**

| Estratégia | RPO | Perda Máxima |
|------------|-----|--------------|
| Full semanal + Incremental diário | 24 horas | 1 dia de dados |
| Full diário | 24 horas | 1 dia de dados |
| Continuous WAL archiving | 5 minutos | Mínima |

---

## 🔒 Segurança

### Proteção de Backups

```bash
# 1. Permissões restritas (Linux)
chmod 600 /backups/inhire/full/*.dump.gz
chown postgres:postgres /backups/inhire/full/*

# 2. Criptografia (opcional)
# Encrypt antes de upload S3
gpg --symmetric --cipher-algo AES256 backup.dump.gz

# Decrypt antes de restore
gpg backup.dump.gz.gpg
```

### Senha do Banco

```bash
# Usar arquivo .pgpass (Linux)
echo "localhost:5432:inhire:postgres:SENHA" > ~/.pgpass
chmod 600 ~/.pgpass

# Windows: Variável de ambiente
setx PGPASSWORD "sua_senha"
```

---

## 📈 Monitoramento

### Verificar Status dos Backups

```powershell
# Windows - Últimos backups
Get-ChildItem "G:\Meu Drive\Framework_Data\Inhire\backups\full" | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Linux
ls -lth /backups/inhire/full | head -5
```

### Ver Logs

```powershell
# Windows
Get-Content "G:\Meu Drive\Framework_Data\Inhire\backups\logs\backup_$(Get-Date -Format 'yyyyMM').log" -Tail 50

# Linux
tail -50 /backups/inhire/logs/backup.log
```

### Alertas Configurados

✅ **Sucesso:** Notificação Slack
❌ **Falha:** Notificação Slack + Email
⚠️ **Warning:** Notificação Slack

---

## 🧪 Teste de Recovery

### Checklist Mensal

- [ ] Backup full executado com sucesso
- [ ] Arquivo de backup existe e não está corrompido
- [ ] Teste de restore passou (database temporário)
- [ ] Contagem de tabelas confere (15 tabelas esperadas)
- [ ] Notificações Slack recebidas
- [ ] Logs sem erros críticos
- [ ] Backups antigos foram removidos (retenção OK)
- [ ] Backup enviado para S3 (se habilitado)

### Simulação de Desastre (Trimestral)

```bash
# 1. Fazer backup do banco atual
./backup_database.sh full

# 2. Simular perda (DROP DATABASE - CUIDADO!)
dropdb -U postgres inhire

# 3. Recriar database
createdb -U postgres inhire

# 4. Restore do backup
./backup_database.sh restore /backups/inhire/full/inhire_full_latest.dump.gz

# 5. Verificar integridade
psql -U postgres -d inhire -c "SELECT COUNT(*) FROM vagas;"
psql -U postgres -d inhire -c "SELECT COUNT(*) FROM candidaturas;"

# 6. Testar sync
python run_sync.py --incremental

# 7. Validar dashboards e queries
```

---

## 🚨 Troubleshooting

### Backup falha com erro de permissão

```bash
# Windows - Executar PowerShell como Administrador

# Linux - Verificar permissões
ls -la /backups/inhire
sudo chown -R postgres:postgres /backups/inhire
```

### Backup muito lento (> 30 min)

```sql
-- Verificar se há locks no banco
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Verificar tamanho das tabelas
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Restore falha com erro de schema

```bash
# Opção 1: Limpar database antes
psql -U postgres -d inhire -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Opção 2: Usar flag --clean no pg_restore
pg_restore --clean --if-exists -d inhire backup.dump
```

### Backup file corrompido

```bash
# Testar integridade
gunzip -t backup.dump.gz  # Linux
# Windows: Extrair e re-comprimir

# Se corrompido, usar backup anterior
./backup_database.sh restore /backups/inhire/full/inhire_full_YYYYMMDD.dump.gz
```

---

## 📝 Melhores Práticas

1. ✅ **Testar restore mensalmente** - Backup não testado = Sem backup
2. ✅ **Manter 30 dias de full backups** - Para casos de corrupção tardia
3. ✅ **Manter 7 dias de incrementais** - Para recovery recente
4. ✅ **Enviar para cloud (S3)** - Proteção contra perda do disco local
5. ✅ **Monitorar espaço em disco** - Alerta se < 20% livre
6. ✅ **Documentar runbooks** - Procedimentos claros de recovery
7. ✅ **Simular desastres trimestralmente** - Validar processo completo

---

## 🔗 Integração com Alertas

O sistema de backup está integrado com o monitoramento:

```yaml
# Alertmanager recebe notificações de:
- Backup falhou (critical)
- Backup muito lento (warning)
- Teste de restore falhou (critical)
- Espaço em disco baixo (warning)
```

Ver: `docs/MONITORING_GUIDE.md`

---

## 📚 Comandos Rápidos

```bash
# Full backup NOW
./backup_database.sh full

# Incremental backup NOW
./backup_database.sh incremental

# Restore latest
./backup_database.sh restore /backups/inhire/full/inhire_full_latest.dump.gz

# Test restore
./backup_database.sh test

# Ver logs
tail -f /backups/inhire/logs/backup.log

# Listar backups disponíveis
ls -lh /backups/inhire/full/

# Ver tamanho total dos backups
du -sh /backups/inhire/
```

---

**Documentação criada em:** 16/01/2026
**Última atualização:** 16/01/2026
**Responsável:** Framework Digital DevOps Team
