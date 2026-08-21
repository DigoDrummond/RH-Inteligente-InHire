@echo off
REM ============================================================================
REM EXPORT CANDIDATURAS - Exportação view vw_relatorio_candidaturas
REM Duração: ~15 segundos
REM Frequência: Diário 09:30 ou manual
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo EXPORT CANDIDATURAS - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando Export Candidaturas >> logs\rotinas.log

python scripts/export/export_relatorio_candidaturas.py >> logs\export_candidaturas.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: Export Candidaturas falhou! >> logs\rotinas.log
    echo ERRO: Export Candidaturas falhou!
    exit /b 1
) else (
    echo [%date% %time%] Export Candidaturas concluido com sucesso >> logs\rotinas.log
    echo Export Candidaturas concluido com sucesso

    REM Enviar notificacao via Google Chat Webhook
    python scripts\webhooks\send_candidaturas_webhook.py
)
