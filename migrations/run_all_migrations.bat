@echo off
REM ========================================
REM Script para Executar Todas as Migrations
REM ========================================

echo.
echo ========================================
echo   EXECUTANDO MIGRATIONS - INHIRE
echo ========================================
echo.

set PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"
set PGUSER=postgres
set PGDATABASE=inhire
set MIGRATIONS_DIR=%~dp0

echo [1/3] Executando Migration 001 - Campos Calculados...
%PSQL% -U %PGUSER% -d %PGDATABASE% -f "%MIGRATIONS_DIR%001_add_calculated_fields.sql"
if %ERRORLEVEL% NEQ 0 (
    echo ERRO na Migration 001!
    pause
    exit /b 1
)
echo Migration 001 concluida!
echo.

echo [2/3] Executando Migration 002 - Views Materializadas...
%PSQL% -U %PGUSER% -d %PGDATABASE% -f "%MIGRATIONS_DIR%002_create_materialized_views.sql"
if %ERRORLEVEL% NEQ 0 (
    echo ERRO na Migration 002!
    pause
    exit /b 1
)
echo Migration 002 concluida!
echo.

echo [3/3] Executando Migration 003 - Tabela de Metricas...
%PSQL% -U %PGUSER% -d %PGDATABASE% -f "%MIGRATIONS_DIR%003_create_metrics_table.sql"
if %ERRORLEVEL% NEQ 0 (
    echo ERRO na Migration 003!
    pause
    exit /b 1
)
echo Migration 003 concluida!
echo.

echo ========================================
echo   TODAS AS MIGRATIONS CONCLUIDAS!
echo ========================================
echo.

pause
