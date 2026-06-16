# ============================================================================
# Script de Backup Automatizado - InHire PostgreSQL (Windows)
# ============================================================================
# Realiza backups full e incrementais do banco de dados InHire
# Suporta retenção, compressão e notificações
#
# Uso:
#   .\backup_database.ps1 -Mode full
#   .\backup_database.ps1 -Mode incremental
#   .\backup_database.ps1 -Mode restore -BackupFile "path\to\backup.dump"
#   .\backup_database.ps1 -Mode test
#
# Agendamento (Task Scheduler):
#   Nome: InHire Full Backup
#   Trigger: Semanal, Domingo 01:00
#   Action: powershell -File "G:\path\to\backup_database.ps1" -Mode full
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("full", "incremental", "restore", "test")]
    [string]$Mode,

    [Parameter(Mandatory=$false)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Database
$DB_HOST = $env:DB_HOST ?? "localhost"
$DB_PORT = $env:DB_PORT ?? "5432"
$DB_NAME = $env:DB_NAME ?? "inhire"
$DB_USER = $env:DB_USER ?? "postgres"
$DB_PASSWORD = $env:DB_PASSWORD ?? ""

# PostgreSQL bin path
$PG_BIN = "C:\Program Files\PostgreSQL\18\bin"

# Diretórios
$BACKUP_ROOT = "G:\Meu Drive\Framework_Data\Inhire\backups"
$BACKUP_DIR_FULL = "$BACKUP_ROOT\full"
$BACKUP_DIR_INCREMENTAL = "$BACKUP_ROOT\incremental"
$LOG_DIR = "$BACKUP_ROOT\logs"

# Retenção (dias)
$RETENTION_FULL = 30
$RETENTION_INCREMENTAL = 7

# Notificações
$SLACK_WEBHOOK = $env:SLACK_WEBHOOK
$EMAIL_TO = "devops@framework.com"

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"

    Write-Host $logMessage

    # Append to log file
    $logFile = "$LOG_DIR\backup_$(Get-Date -Format 'yyyyMM').log"
    Add-Content -Path $logFile -Value $logMessage
}

function Send-SlackNotification {
    param(
        [string]$Message,
        [string]$Color = "good"
    )

    if (-not $SLACK_WEBHOOK) {
        return
    }

    $payload = @{
        attachments = @(
            @{
                color = $Color
                title = "InHire Backup"
                text = $Message
                footer = $env:COMPUTERNAME
                ts = [int][double]::Parse((Get-Date -UFormat %s))
            }
        )
    } | ConvertTo-Json -Depth 3

    try {
        Invoke-RestMethod -Uri $SLACK_WEBHOOK -Method Post -Body $payload -ContentType 'application/json' | Out-Null
    } catch {
        Write-Log "WARN" "Failed to send Slack notification: $_"
    }
}

function Test-Prerequisites {
    Write-Log "INFO" "Verificando pré-requisitos..."

    # Verificar pg_dump
    if (-not (Test-Path "$PG_BIN\pg_dump.exe")) {
        Write-Log "ERROR" "pg_dump não encontrado em $PG_BIN"
        exit 1
    }

    # Criar diretórios
    @($BACKUP_DIR_FULL, $BACKUP_DIR_INCREMENTAL, $LOG_DIR) | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
        }
    }

    # Verificar conectividade
    $env:PGPASSWORD = $DB_PASSWORD
    $result = & "$PG_BIN\psql.exe" -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Não foi possível conectar ao banco de dados: $result"
        exit 1
    }

    Write-Log "INFO" "Pré-requisitos OK"
}

function Get-DatabaseSize {
    $env:PGPASSWORD = $DB_PASSWORD
    $size = & "$PG_BIN\psql.exe" -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));"
    return $size.Trim()
}

# ============================================================================
# BACKUP FULL
# ============================================================================

function Invoke-FullBackup {
    Write-Log "INFO" "=========================================="
    Write-Log "INFO" "Iniciando FULL BACKUP"
    Write-Log "INFO" "=========================================="

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "$BACKUP_DIR_FULL\inhire_full_$timestamp.dump"
    $backupFileCompressed = "$backupFile.zip"
    $startTime = Get-Date

    $dbSize = Get-DatabaseSize
    Write-Log "INFO" "Tamanho do banco: $dbSize"

    # Realizar backup
    Write-Log "INFO" "Executando pg_dump..."
    $env:PGPASSWORD = $DB_PASSWORD

    & "$PG_BIN\pg_dump.exe" `
        -h $DB_HOST `
        -p $DB_PORT `
        -U $DB_USER `
        -d $DB_NAME `
        -F c `
        -b `
        -v `
        -f $backupFile 2>&1 | Tee-Object -Append -FilePath "$LOG_DIR\backup.log"

    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Backup falhou!"
        Send-SlackNotification "❌ Backup FULL falhou" "danger"
        exit 1
    }

    # Comprimir
    Write-Log "INFO" "Comprimindo backup..."
    Compress-Archive -Path $backupFile -DestinationPath $backupFileCompressed -CompressionLevel Optimal
    Remove-Item $backupFile

    $backupSize = (Get-Item $backupFileCompressed).Length / 1MB
    $backupSizeStr = "{0:N2} MB" -f $backupSize
    $duration = ((Get-Date) - $startTime).TotalSeconds

    Write-Log "INFO" "Backup completo: $backupFileCompressed"
    Write-Log "INFO" "Tamanho: $backupSizeStr"
    Write-Log "INFO" "Duração: $([math]::Round($duration))s"

    # Verificar integridade
    Write-Log "INFO" "Verificando integridade..."
    $testResult = Test-Archive -Path $backupFileCompressed
    if (-not $testResult) {
        Write-Log "ERROR" "Backup corrompido!"
        Send-SlackNotification "❌ Backup FULL corrompido" "danger"
        exit 1
    }

    # Criar link para latest
    $latestLink = "$BACKUP_DIR_FULL\inhire_full_latest.dump.zip"
    if (Test-Path $latestLink) {
        Remove-Item $latestLink
    }
    Copy-Item $backupFileCompressed $latestLink

    # Cleanup antigos
    Write-Log "INFO" "Removendo backups antigos (> $RETENTION_FULL dias)..."
    $cutoffDate = (Get-Date).AddDays(-$RETENTION_FULL)
    Get-ChildItem "$BACKUP_DIR_FULL\inhire_full_*.dump.zip" | Where-Object {
        $_.LastWriteTime -lt $cutoffDate
    } | Remove-Item -Force

    # Notificação
    $message = "✅ Backup FULL concluído`nTamanho: $backupSizeStr`nDuração: $([math]::Round($duration))s`nDB Size: $dbSize"
    Send-SlackNotification $message "good"

    Write-Log "INFO" "=========================================="
    Write-Log "INFO" "FULL BACKUP CONCLUÍDO COM SUCESSO"
    Write-Log "INFO" "=========================================="
}

function Test-Archive {
    param([string]$Path)

    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
        $zip.Dispose()
        return $true
    } catch {
        return $false
    }
}

# ============================================================================
# BACKUP INCREMENTAL
# ============================================================================

function Invoke-IncrementalBackup {
    Write-Log "INFO" "=========================================="
    Write-Log "INFO" "Iniciando BACKUP INCREMENTAL"
    Write-Log "INFO" "=========================================="

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "$BACKUP_DIR_INCREMENTAL\inhire_incr_$timestamp.dump"
    $backupFileCompressed = "$backupFile.zip"
    $startTime = Get-Date

    # Realizar backup
    Write-Log "INFO" "Executando pg_dump incremental..."
    $env:PGPASSWORD = $DB_PASSWORD

    & "$PG_BIN\pg_dump.exe" `
        -h $DB_HOST `
        -p $DB_PORT `
        -U $DB_USER `
        -d $DB_NAME `
        -F c `
        -f $backupFile 2>&1 | Tee-Object -Append -FilePath "$LOG_DIR\backup.log"

    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Backup incremental falhou!"
        Send-SlackNotification "⚠️ Backup INCREMENTAL falhou" "warning"
        exit 1
    }

    # Comprimir
    Compress-Archive -Path $backupFile -DestinationPath $backupFileCompressed -CompressionLevel Optimal
    Remove-Item $backupFile

    $backupSize = (Get-Item $backupFileCompressed).Length / 1MB
    $backupSizeStr = "{0:N2} MB" -f $backupSize
    $duration = ((Get-Date) - $startTime).TotalSeconds

    Write-Log "INFO" "Backup incremental completo: $backupSizeStr em $([math]::Round($duration))s"

    # Cleanup antigos
    $cutoffDate = (Get-Date).AddDays(-$RETENTION_INCREMENTAL)
    Get-ChildItem "$BACKUP_DIR_INCREMENTAL\inhire_incr_*.dump.zip" | Where-Object {
        $_.LastWriteTime -lt $cutoffDate
    } | Remove-Item -Force

    Send-SlackNotification "✅ Backup INCREMENTAL concluído ($backupSizeStr)" "good"

    Write-Log "INFO" "=========================================="
    Write-Log "INFO" "BACKUP INCREMENTAL CONCLUÍDO"
    Write-Log "INFO" "=========================================="
}

# ============================================================================
# RESTORE
# ============================================================================

function Invoke-Restore {
    param([string]$BackupPath)

    Write-Log "INFO" "=========================================="
    Write-Log "INFO" "Iniciando RESTORE"
    Write-Log "INFO" "=========================================="

    if (-not (Test-Path $BackupPath)) {
        Write-Log "ERROR" "Arquivo de backup não encontrado: $BackupPath"
        exit 1
    }

    Write-Host "ATENÇÃO: Isso irá SOBRESCREVER o banco de dados atual!" -ForegroundColor Yellow
    $confirm = Read-Host "Tem certeza? (yes/no)"

    if ($confirm -ne "yes") {
        Write-Log "INFO" "Restore cancelado"
        exit 0
    }

    # Descomprimir
    Write-Log "INFO" "Descomprimindo backup..."
    $tempDir = "$env:TEMP\inhire_restore_$(Get-Date -Format 'yyyyMMddHHmmss')"
    Expand-Archive -Path $BackupPath -DestinationPath $tempDir -Force

    $dumpFile = Get-ChildItem "$tempDir\*.dump" | Select-Object -First 1

    # Fazer restore
    Write-Log "INFO" "Executando pg_restore..."
    $env:PGPASSWORD = $DB_PASSWORD

    & "$PG_BIN\pg_restore.exe" `
        -h $DB_HOST `
        -p $DB_PORT `
        -U $DB_USER `
        -d $DB_NAME `
        -c `
        -v `
        $dumpFile.FullName 2>&1 | Tee-Object -Append -FilePath "$LOG_DIR\restore.log"

    if ($LASTEXITCODE -eq 0) {
        Write-Log "INFO" "Restore concluído com sucesso"
        Send-SlackNotification "✅ Restore concluído" "good"
    } else {
        Write-Log "ERROR" "Restore falhou"
        Send-SlackNotification "❌ Restore falhou" "danger"
        exit 1
    }

    # Cleanup
    Remove-Item $tempDir -Recurse -Force

    Write-Log "INFO" "=========================================="
    Write-Log "INFO" "RESTORE CONCLUÍDO"
    Write-Log "INFO" "=========================================="
}

# ============================================================================
# TESTE DE RESTORE
# ============================================================================

function Invoke-TestRestore {
    Write-Log "INFO" "=========================================="
    Write-Log "INFO" "Iniciando TESTE DE RESTORE"
    Write-Log "INFO" "=========================================="

    $latestBackup = "$BACKUP_DIR_FULL\inhire_full_latest.dump.zip"

    if (-not (Test-Path $latestBackup)) {
        Write-Log "ERROR" "Backup mais recente não encontrado"
        exit 1
    }

    # Criar database temporário
    $testDb = "inhire_test_restore_$(Get-Date -Format 'yyyyMMddHHmmss')"

    Write-Log "INFO" "Criando database temporário: $testDb"
    $env:PGPASSWORD = $DB_PASSWORD
    & "$PG_BIN\createdb.exe" -h $DB_HOST -p $DB_PORT -U $DB_USER $testDb

    # Descomprimir e restaurar
    $tempDir = "$env:TEMP\inhire_test_$(Get-Date -Format 'yyyyMMddHHmmss')"
    Expand-Archive -Path $latestBackup -DestinationPath $tempDir -Force
    $dumpFile = Get-ChildItem "$tempDir\*.dump" | Select-Object -First 1

    Write-Log "INFO" "Restaurando backup em $testDb..."
    & "$PG_BIN\pg_restore.exe" `
        -h $DB_HOST `
        -p $DB_PORT `
        -U $DB_USER `
        -d $testDb `
        $dumpFile.FullName 2>&1 | Tee-Object -Append -FilePath "$LOG_DIR\test_restore.log"

    if ($LASTEXITCODE -eq 0) {
        Write-Log "INFO" "✅ Teste de restore PASSOU"

        # Verificar integridade
        $tableCount = & "$PG_BIN\psql.exe" -h $DB_HOST -p $DB_PORT -U $DB_USER -d $testDb -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
        $tableCount = $tableCount.Trim()

        Write-Log "INFO" "Tabelas restauradas: $tableCount"
        Send-SlackNotification "✅ Teste de restore PASSOU ($tableCount tabelas)" "good"
    } else {
        Write-Log "ERROR" "❌ Teste de restore FALHOU"
        Send-SlackNotification "❌ Teste de restore FALHOU" "danger"
    }

    # Cleanup
    Write-Log "INFO" "Removendo database temporário..."
    & "$PG_BIN\dropdb.exe" -h $DB_HOST -p $DB_PORT -U $DB_USER $testDb
    Remove-Item $tempDir -Recurse -Force

    Write-Log "INFO" "=========================================="
    Write-Log "INFO" "TESTE DE RESTORE CONCLUÍDO"
    Write-Log "INFO" "=========================================="
}

# ============================================================================
# MAIN
# ============================================================================

Test-Prerequisites

switch ($Mode) {
    "full" {
        Invoke-FullBackup
    }
    "incremental" {
        Invoke-IncrementalBackup
    }
    "restore" {
        if (-not $BackupFile) {
            Write-Host "Erro: -BackupFile é obrigatório para restore"
            exit 1
        }
        Invoke-Restore -BackupPath $BackupFile
    }
    "test" {
        Invoke-TestRestore
    }
}
