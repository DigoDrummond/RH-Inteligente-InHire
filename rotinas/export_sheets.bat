@echo off
REM ============================================================================
REM EXPORT SHEETS - Exportação Principal para Google Sheets
REM Duração: ~10-20 segundos
REM Frequência: Após sync (08:30, 20:30) ou manual
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo EXPORT SHEETS - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Export Google Sheets >> logs\rotinas.log

python scripts/export/export_views_oauth.py >> logs\export.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: Export Sheets falhou! >> logs\rotinas.log
    echo ERRO: Export Sheets falhou!
    exit /b 1
) else (
    echo [%date% %time%] Export Sheets concluido com sucesso >> logs\rotinas.log
    echo Export Sheets concluido com sucesso
)
