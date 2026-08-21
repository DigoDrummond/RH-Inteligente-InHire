@echo off
REM ============================================================================
REM EXPORT ANALISE POSICOES - Exportação view vw_analise_posicoes
REM Duração: ~15 segundos
REM Frequência: Diário 09:00 ou manual
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo EXPORT ANALISE POSICOES - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Export Analise Posicoes >> logs\rotinas.log

python scripts/export/export_analise_posicoes.py >> logs\export_analise.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: Export Analise falhou! >> logs\rotinas.log
    echo ERRO: Export Analise falhou!
    exit /b 1
) else (
    echo [%date% %time%] Export Analise concluido com sucesso >> logs\rotinas.log
    echo Export Analise concluido com sucesso
)
