@echo off
REM Script de teste rapido de backup (sem pause)

setlocal enabledelayedexpansion

set "PSQL_BIN=C:\Program Files\PostgreSQL\18\bin"
set "PROJECT_ROOT=%~dp0..\.."
set "BACKUP_ROOT=%PROJECT_ROOT%\Backup_BD_Inhire"
set "ENV_FILE=%PROJECT_ROOT%\.env"

set "DB_HOST=localhost"
set "DB_PORT=5432"
set "DB_NAME=inhire"
set "DB_USER=postgres"

echo [TEST] Iniciando teste de backup...
echo [TEST] Validando pre-requisitos...

if not exist "%PSQL_BIN%\pg_dump.exe" (
    echo [ERRO] pg_dump.exe nao encontrado
    exit /b 1
)
echo [OK] pg_dump.exe encontrado

if not exist "%ENV_FILE%" (
    echo [ERRO] Arquivo .env nao encontrado
    exit /b 1
)
echo [OK] Arquivo .env encontrado

for /f "usebackq tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
    if "%%a"=="DB_PASSWORD" set "DB_PASSWORD=%%b"
)

if "%DB_PASSWORD%"=="" (
    echo [ERRO] DB_PASSWORD nao encontrada
    exit /b 1
)
echo [OK] Credenciais carregadas

if not exist "%BACKUP_ROOT%\full" mkdir "%BACKUP_ROOT%\full"
echo [OK] Diretorios verificados

set "PGPASSWORD=%DB_PASSWORD%"
"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -c "SELECT version();" > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Falha ao conectar ao banco
    set "PGPASSWORD="
    exit /b 1
)
echo [OK] Conexao estabelecida

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "BACKUP_FULL=%BACKUP_ROOT%\full\inhire_test_%TIMESTAMP%.dump"

echo [TEST] Executando backup custom format...
echo [TEST] Destino: %BACKUP_FULL%

"%PSQL_BIN%\pg_dump.exe" ^
    -U %DB_USER% ^
    -h %DB_HOST% ^
    -p %DB_PORT% ^
    -d %DB_NAME% ^
    -F c ^
    --blobs ^
    --no-owner ^
    --no-privileges ^
    -f "%BACKUP_FULL%" 2>&1

if errorlevel 1 (
    echo [ERRO] Falha no backup
    set "PGPASSWORD="
    exit /b 1
)

if not exist "%BACKUP_FULL%" (
    echo [ERRO] Arquivo nao foi criado
    set "PGPASSWORD="
    exit /b 1
)

for %%A in ("%BACKUP_FULL%") do set "BACKUP_SIZE=%%~zA"
set /a "BACKUP_SIZE_MB=%BACKUP_SIZE% / 1048576"

echo [OK] Backup concluido!
echo [OK] Arquivo: %BACKUP_FULL%
echo [OK] Tamanho: %BACKUP_SIZE_MB% MB (%BACKUP_SIZE% bytes)

set "PGPASSWORD="
echo [TEST] Teste concluido com sucesso!
exit /b 0
