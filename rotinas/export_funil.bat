@echo off
REM ============================================================================
REM EXPORT FUNIL PERFORMANCE - Exportação view vw_funil_performance
REM Duração: ~20 segundos
REM Frequência: Semanal (Segunda 09:00) ou manual
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo EXPORT FUNIL PERFORMANCE - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Export Funil Performance >> logs\rotinas.log

python scripts/export/export_funil_performance.py >> logs\export_funil.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: Export Funil falhou! >> logs\rotinas.log
    echo ERRO: Export Funil falhou!
    exit /b 1
) else (
    echo [%date% %time%] Export Funil concluido com sucesso >> logs\rotinas.log
    echo Export Funil concluido com sucesso
)
