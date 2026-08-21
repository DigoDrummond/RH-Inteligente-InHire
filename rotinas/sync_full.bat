@echo off
REM ============================================================================
REM SYNC FULL - Sincronização Completa (100% dos dados)
REM Duração: ~55 minutos
REM Frequência: 1x/semana (Domingo 02:00)
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo SYNC FULL - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Sync FULL >> logs\rotinas.log

python run_sync.py --full >> logs\sync_full.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: Sync FULL falhou! >> logs\rotinas.log
    echo ERRO: Sync FULL falhou!
    exit /b 1
) else (
    echo [%date% %time%] Sync FULL concluido com sucesso >> logs\rotinas.log
    echo Sync FULL concluido com sucesso
)
