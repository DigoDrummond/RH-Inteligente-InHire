@echo off
REM ============================================================================
REM ROTINA SEMANAL (DOMINGO) - Backup + Sync FULL + Exports
REM Duração Total: ~70 minutos (10 min backup + 55 min sync + 5 min exports)
REM Frequência: Domingos 02:00
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo ROTINA SEMANAL INHIRE - %date% %time%
echo ============================================================================
echo.

REM 1. Backup
echo [1/3] Executando Backup BD...
call rotinas\backup_bd.bat
if errorlevel 1 (
    echo ERRO: Backup falhou!
    exit /b 1
)
echo.

REM 2. Sync FULL
echo [2/3] Executando Sync FULL (pode levar 55 min)...
call rotinas\sync_full.bat
if errorlevel 1 (
    echo ERRO: Sync FULL falhou!
    exit /b 1
)
echo.

REM 3. Export Sheets
echo [3/3] Exportando para Google Sheets...
call rotinas\export_sheets.bat
echo.

echo ============================================================================
echo ROTINA SEMANAL CONCLUIDA - %date% %time%
echo ============================================================================
