@echo off
REM ============================================================================
REM BACKUP BD - Backup Completo do Banco de Dados PostgreSQL
REM Duração: ~5-10 minutos
REM Frequência: Diário 01:00 (ANTES de qualquer sync)
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo BACKUP BD - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Backup BD >> logs\rotinas.log

call "scripts\backup\backup_inhire_windows.bat" >> logs\backup.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: Backup BD falhou! >> logs\rotinas.log
    echo ERRO: Backup BD falhou!
    exit /b 1
) else (
    echo [%date% %time%] Backup BD concluido com sucesso >> logs\rotinas.log
    echo Backup BD concluido com sucesso
)
