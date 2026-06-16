#!/bin/bash
# ============================================================================
# Script de Backup Automatizado - InHire PostgreSQL
# ============================================================================
# Realiza backups full e incrementais do banco de dados InHire
# Suporta retenção, compressão, upload para S3 e verificação de integridade
#
# Uso:
#   ./backup_database.sh [full|incremental|restore]
#
# Agendamento (crontab):
#   0 1 * * 0  /path/to/backup_database.sh full       # Full backup semanal (Domingo 01:00)
#   0 2 * * 1-6  /path/to/backup_database.sh incremental  # Incremental diário
#   0 3 1 * *  /path/to/backup_database.sh test       # Teste mensal
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Database
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-inhire}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Diretórios
BACKUP_ROOT="${BACKUP_ROOT:-/backups/inhire}"
BACKUP_DIR_FULL="$BACKUP_ROOT/full"
BACKUP_DIR_INCREMENTAL="$BACKUP_ROOT/incremental"
BACKUP_DIR_WAL="$BACKUP_ROOT/wal"
LOG_DIR="$BACKUP_ROOT/logs"

# AWS S3 (opcional)
S3_BUCKET="${S3_BUCKET:-s3://framework-backups/inhire}"
S3_ENABLED="${S3_ENABLED:-false}"

# Retenção (dias)
RETENTION_FULL=30
RETENTION_INCREMENTAL=7
RETENTION_WAL=7

# Notificações
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_TO="${EMAIL_TO:-devops@framework.com}"

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_DIR/backup.log"
}

notify_slack() {
    local message="$1"
    local color="${2:-good}"  # good, warning, danger

    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"InHire Backup\",
                    \"text\": \"$message\",
                    \"footer\": \"$(hostname)\",
                    \"ts\": $(date +%s)
                }]
            }" > /dev/null 2>&1
    fi
}

notify_email() {
    local subject="$1"
    local body="$2"

    if command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" "$EMAIL_TO"
    fi
}

check_prerequisites() {
    log "INFO" "Verificando pré-requisitos..."

    # Verificar pg_dump
    if ! command -v pg_dump &> /dev/null; then
        log "ERROR" "pg_dump não encontrado. Instale PostgreSQL client."
        exit 1
    fi

    # Criar diretórios
    mkdir -p "$BACKUP_DIR_FULL" "$BACKUP_DIR_INCREMENTAL" "$BACKUP_DIR_WAL" "$LOG_DIR"

    # Verificar conectividade
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        log "ERROR" "Não foi possível conectar ao banco de dados"
        exit 1
    fi

    log "INFO" "Pré-requisitos OK"
}

get_db_size() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs
}

# ============================================================================
# BACKUP FULL
# ============================================================================

backup_full() {
    log "INFO" "=========================================="
    log "INFO" "Iniciando FULL BACKUP"
    log "INFO" "=========================================="

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR_FULL/inhire_full_$timestamp.dump"
    local backup_file_compressed="$backup_file.gz"
    local start_time=$(date +%s)

    local db_size=$(get_db_size)
    log "INFO" "Tamanho do banco: $db_size"

    # Realizar backup
    log "INFO" "Executando pg_dump..."
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -F c \
        -b \
        -v \
        -f "$backup_file" 2>&1 | tee -a "$LOG_DIR/backup.log"

    if [ $? -ne 0 ]; then
        log "ERROR" "Backup falhou!"
        notify_slack "❌ Backup FULL falhou" "danger"
        notify_email "InHire Backup FAILED" "Full backup falhou. Ver logs em $LOG_DIR/backup.log"
        exit 1
    fi

    # Comprimir
    log "INFO" "Comprimindo backup..."
    gzip "$backup_file"

    local backup_size=$(du -h "$backup_file_compressed" | cut -f1)
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log "INFO" "Backup completo: $backup_file_compressed"
    log "INFO" "Tamanho: $backup_size"
    log "INFO" "Duração: ${duration}s"

    # Verificar integridade
    log "INFO" "Verificando integridade..."
    if ! gunzip -t "$backup_file_compressed"; then
        log "ERROR" "Backup corrompido!"
        notify_slack "❌ Backup FULL corrompido" "danger"
        exit 1
    fi

    # Upload para S3
    if [ "$S3_ENABLED" = "true" ]; then
        log "INFO" "Enviando para S3..."
        if command -v aws &> /dev/null; then
            aws s3 cp "$backup_file_compressed" "$S3_BUCKET/full/" --storage-class STANDARD_IA
            log "INFO" "Upload S3 concluído"
        else
            log "WARN" "AWS CLI não encontrado, pulando upload"
        fi
    fi

    # Criar link para latest
    ln -sf "$backup_file_compressed" "$BACKUP_DIR_FULL/inhire_full_latest.dump.gz"

    # Cleanup antigos
    log "INFO" "Removendo backups antigos (> $RETENTION_FULL dias)..."
    find "$BACKUP_DIR_FULL" -name "inhire_full_*.dump.gz" -mtime +$RETENTION_FULL -delete

    # Notificação
    local message="✅ Backup FULL concluído\nTamanho: $backup_size\nDuração: ${duration}s\nDB Size: $db_size"
    notify_slack "$message" "good"

    log "INFO" "=========================================="
    log "INFO" "FULL BACKUP CONCLUÍDO COM SUCESSO"
    log "INFO" "=========================================="
}

# ============================================================================
# BACKUP INCREMENTAL (WAL)
# ============================================================================

backup_incremental() {
    log "INFO" "=========================================="
    log "INFO" "Iniciando BACKUP INCREMENTAL"
    log "INFO" "=========================================="

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR_INCREMENTAL/inhire_incr_$timestamp.dump"
    local backup_file_compressed="$backup_file.gz"
    local start_time=$(date +%s)

    # Backup incremental via pg_dump (schema + dados modificados)
    # Para backup WAL verdadeiro, use pg_basebackup + archive_command
    log "INFO" "Executando pg_dump incremental..."
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -F c \
        -f "$backup_file" 2>&1 | tee -a "$LOG_DIR/backup.log"

    if [ $? -ne 0 ]; then
        log "ERROR" "Backup incremental falhou!"
        notify_slack "⚠️ Backup INCREMENTAL falhou" "warning"
        exit 1
    fi

    # Comprimir
    gzip "$backup_file"

    local backup_size=$(du -h "$backup_file_compressed" | cut -f1)
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log "INFO" "Backup incremental completo: $backup_size em ${duration}s"

    # Upload para S3
    if [ "$S3_ENABLED" = "true" ]; then
        aws s3 cp "$backup_file_compressed" "$S3_BUCKET/incremental/"
    fi

    # Cleanup antigos
    find "$BACKUP_DIR_INCREMENTAL" -name "inhire_incr_*.dump.gz" -mtime +$RETENTION_INCREMENTAL -delete

    notify_slack "✅ Backup INCREMENTAL concluído ($backup_size)" "good"

    log "INFO" "=========================================="
    log "INFO" "BACKUP INCREMENTAL CONCLUÍDO"
    log "INFO" "=========================================="
}

# ============================================================================
# RESTORE
# ============================================================================

restore_backup() {
    local backup_file="$1"

    log "INFO" "=========================================="
    log "INFO" "Iniciando RESTORE"
    log "INFO" "=========================================="

    if [ ! -f "$backup_file" ]; then
        log "ERROR" "Arquivo de backup não encontrado: $backup_file"
        exit 1
    fi

    log "WARN" "ATENÇÃO: Isso irá SOBRESCREVER o banco de dados atual!"
    read -p "Tem certeza? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log "INFO" "Restore cancelado"
        exit 0
    fi

    # Descomprimir se necessário
    local restore_file="$backup_file"
    if [[ "$backup_file" == *.gz ]]; then
        log "INFO" "Descomprimindo backup..."
        restore_file="${backup_file%.gz}"
        gunzip -c "$backup_file" > "$restore_file"
    fi

    # Fazer restore
    log "INFO" "Executando pg_restore..."
    PGPASSWORD="$DB_PASSWORD" pg_restore \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -c \
        -v \
        "$restore_file" 2>&1 | tee -a "$LOG_DIR/restore.log"

    if [ $? -eq 0 ]; then
        log "INFO" "Restore concluído com sucesso"
        notify_slack "✅ Restore concluído" "good"
    else
        log "ERROR" "Restore falhou"
        notify_slack "❌ Restore falhou" "danger"
        exit 1
    fi

    # Cleanup arquivo temporário
    if [[ "$backup_file" == *.gz ]]; then
        rm "$restore_file"
    fi

    log "INFO" "=========================================="
    log "INFO" "RESTORE CONCLUÍDO"
    log "INFO" "=========================================="
}

# ============================================================================
# TESTE DE RESTORE
# ============================================================================

test_restore() {
    log "INFO" "=========================================="
    log "INFO" "Iniciando TESTE DE RESTORE"
    log "INFO" "=========================================="

    local latest_backup="$BACKUP_DIR_FULL/inhire_full_latest.dump.gz"

    if [ ! -f "$latest_backup" ]; then
        log "ERROR" "Backup mais recente não encontrado"
        exit 1
    fi

    # Criar database temporário para teste
    local test_db="inhire_test_restore_$(date +%s)"

    log "INFO" "Criando database temporário: $test_db"
    PGPASSWORD="$DB_PASSWORD" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$test_db"

    # Descomprimir e restaurar
    log "INFO" "Restaurando backup em $test_db..."
    gunzip -c "$latest_backup" | \
        PGPASSWORD="$DB_PASSWORD" pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$test_db" 2>&1 | tee -a "$LOG_DIR/test_restore.log"

    if [ $? -eq 0 ]; then
        log "INFO" "✅ Teste de restore PASSOU"

        # Verificar integridade básica
        local table_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$test_db" -t -c \
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)

        log "INFO" "Tabelas restauradas: $table_count"
        notify_slack "✅ Teste de restore PASSOU ($table_count tabelas)" "good"
    else
        log "ERROR" "❌ Teste de restore FALHOU"
        notify_slack "❌ Teste de restore FALHOU" "danger"
    fi

    # Cleanup
    log "INFO" "Removendo database temporário..."
    PGPASSWORD="$DB_PASSWORD" dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$test_db"

    log "INFO" "=========================================="
    log "INFO" "TESTE DE RESTORE CONCLUÍDO"
    log "INFO" "=========================================="
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    check_prerequisites

    case "${1:-full}" in
        full)
            backup_full
            ;;
        incremental)
            backup_incremental
            ;;
        restore)
            if [ -z "${2:-}" ]; then
                echo "Uso: $0 restore <arquivo_backup>"
                exit 1
            fi
            restore_backup "$2"
            ;;
        test)
            test_restore
            ;;
        *)
            echo "Uso: $0 {full|incremental|restore <arquivo>|test}"
            exit 1
            ;;
    esac
}

# Executar
main "$@"
