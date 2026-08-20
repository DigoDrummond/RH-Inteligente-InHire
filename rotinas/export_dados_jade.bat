@echo off
REM ============================================================================
REM EXPORT DADOS JADE - Exportação view vw_dados_jade
REM Duração: ~10 segundos
REM Frequência: Diário 09:15 ou manual
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo EXPORT DADOS JADE - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Export Dados Jade >> logs\rotinas.log

python scripts/export/export_dados_jade.py >> logs\export_jade.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: Export Jade falhou! >> logs\rotinas.log
    echo ERRO: Export Jade falhou!
    exit /b 1
) else (
    echo [%date% %time%] Export Jade concluido com sucesso >> logs\rotinas.log
    echo Export Jade concluido com sucesso
)
