@echo off
REM ============================================================================
REM HEALTH CHECK - Verificação de Saúde do Sistema
REM Duração: <1 minuto
REM Frequência: Diário 06:00
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo HEALTH CHECK - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Health Check >> logs\rotinas.log

python health_check.py >> logs\health_check.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] AVISO: Health Check encontrou problemas >> logs\rotinas.log
    echo AVISO: Health Check encontrou problemas
    exit /b 1
) else (
    echo [%date% %time%] Health Check concluido - Sistema saudavel >> logs\rotinas.log
    echo Health Check concluido - Sistema saudavel
)
