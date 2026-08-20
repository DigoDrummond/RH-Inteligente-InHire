@echo off
REM ============================================================================
REM ROTINA DIARIA - Sync Incremental + Exports
REM Duração Total: ~50 minutos
REM Frequência: Segunda a Sábado 08:00 e 20:00
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo ROTINA DIARIA INHIRE - %date% %time%
echo ============================================================================
echo.

REM 1. Sync Incremental
echo [1/5] Executando Sync INCREMENTAL...
call rotinas\sync_incremental.bat
if errorlevel 1 (
    echo ERRO: Sync INCREMENTAL falhou!
    exit /b 1
)
echo.

REM 2. Export Sheets Principal
echo [2/5] Exportando para Google Sheets...
call rotinas\export_sheets.bat
echo.

REM 3. Export Análise Posições
echo [3/5] Exportando Analise Posicoes...
call rotinas\export_analise_posicoes.bat
echo.

REM 4. Export Dados Jade
echo [4/5] Exportando Dados Jade...
call rotinas\export_dados_jade.bat
echo.

REM 5. Export Candidaturas
echo [5/5] Exportando Candidaturas...
call rotinas\export_candidaturas.bat
echo.

echo ============================================================================
echo ROTINA DIARIA CONCLUIDA - %date% %time%
echo ============================================================================
