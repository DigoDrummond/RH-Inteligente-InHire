@echo off
REM ============================================================================
REM SYNC INCREMENTAL - Sincronização Incremental (apenas dados modificados)
REM Duração: ~40-50 minutos
REM Frequência: 2x/dia (08:00 e 20:00)
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo SYNC INCREMENTAL - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Sync INCREMENTAL >> logs\rotinas.log

python sync_incremental_completo.py --completa --yes >> logs\sync_incremental.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: Sync INCREMENTAL falhou! >> logs\rotinas.log
    echo ERRO: Sync INCREMENTAL falhou!
    exit /b 1
) else (
    echo [%date% %time%] Sync INCREMENTAL concluido com sucesso >> logs\rotinas.log
    echo Sync INCREMENTAL concluido com sucesso
)
