@echo off
REM ============================================================================
REM Script de Backup Completo - Banco de Dados Inhire
REM ============================================================================
REM Autor: Auto-gerado
REM Data: 2026-03-23
REM Descrição: Backup completo do PostgreSQL database 'inhire'
REM ============================================================================

setlocal enabledelayedexpansion

REM ============================================================================
REM CONFIGURAÇÕES
REM ============================================================================

REM Caminhos
set "PSQL_BIN=C:\Program Files\PostgreSQL\18\bin"
set "PROJECT_ROOT=%~dp0..\.."
set "BACKUP_ROOT=%PROJECT_ROOT%\Backup_BD_Inhire"
set "ENV_FILE=%PROJECT_ROOT%\.env"

REM Configurações do banco
set "DB_HOST=localhost"
set "DB_PORT=5432"
set "DB_NAME=inhire"
set "DB_USER=postgres"

REM Timestamp para nomes de arquivo
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "DATE_ONLY=%dt:~0,4%%dt:~4,2%%dt:~6,2%"

REM Nomes dos arquivos de backup
set "BACKUP_FULL=%BACKUP_ROOT%\full\inhire_backup_%TIMESTAMP%.dump"
set "BACKUP_SQL=%BACKUP_ROOT%\sql\inhire_backup_%TIMESTAMP%.sql"
set "BACKUP_SCHEMA=%BACKUP_ROOT%\schema\inhire_schema_%DATE_ONLY%.sql"
set "BACKUP_DATA=%BACKUP_ROOT%\data\inhire_data_%TIMESTAMP%.dump"
set "LOG_FILE=%BACKUP_ROOT%\logs\backup_%TIMESTAMP%.log"

echo ============================================================================
echo BACKUP COMPLETO DO BANCO DE DADOS INHIRE
echo ============================================================================
echo.
echo Data/Hora: %TIMESTAMP%
echo Database: %DB_NAME%
echo Host: %DB_HOST%:%DB_PORT%
echo Usuario: %DB_USER%
echo.
echo Destino: %BACKUP_ROOT%
echo.
echo ============================================================================
echo.

REM ============================================================================
REM VALIDAÇÕES PRÉ-EXECUÇÃO
REM ============================================================================

echo [INFO] Validando pre-requisitos...
echo [INFO] Validando pre-requisitos... >> "%LOG_FILE%" 2>&1

REM Verificar se pg_dump existe
if not exist "%PSQL_BIN%\pg_dump.exe" (
    echo [ERRO] pg_dump.exe nao encontrado em: %PSQL_BIN%
    echo [ERRO] Verifique a instalacao do PostgreSQL
    echo [ERRO] pg_dump.exe nao encontrado >> "%LOG_FILE%" 2>&1
    pause
    exit /b 1
)
echo [OK] pg_dump.exe encontrado >> "%LOG_FILE%" 2>&1

REM Verificar se arquivo .env existe
if not exist "%ENV_FILE%" (
    echo [ERRO] Arquivo .env nao encontrado em: %ENV_FILE%
    echo [ERRO] Arquivo necessario para obter credenciais do banco
    echo [ERRO] Arquivo .env nao encontrado >> "%LOG_FILE%" 2>&1
    pause
    exit /b 1
)
echo [OK] Arquivo .env encontrado >> "%LOG_FILE%" 2>&1

REM Ler senha do arquivo .env
for /f "usebackq tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
    if "%%a"=="DB_PASSWORD" set "DB_PASSWORD=%%b"
)

if "%DB_PASSWORD%"=="" (
    echo [ERRO] DB_PASSWORD nao encontrada no arquivo .env
    echo [ERRO] DB_PASSWORD nao encontrada no .env >> "%LOG_FILE%" 2>&1
    pause
    exit /b 1
)
echo [OK] Credenciais carregadas do .env >> "%LOG_FILE%" 2>&1

REM Criar diretórios se não existirem
if not exist "%BACKUP_ROOT%\full" mkdir "%BACKUP_ROOT%\full"
if not exist "%BACKUP_ROOT%\sql" mkdir "%BACKUP_ROOT%\sql"
if not exist "%BACKUP_ROOT%\schema" mkdir "%BACKUP_ROOT%\schema"
if not exist "%BACKUP_ROOT%\logs" mkdir "%BACKUP_ROOT%\logs"
if not exist "%BACKUP_ROOT%\latest" mkdir "%BACKUP_ROOT%\latest"
echo [OK] Diretorios criados/verificados >> "%LOG_FILE%" 2>&1

REM Testar conexão com o banco
echo [INFO] Testando conexao com o banco...
set "PGPASSWORD=%DB_PASSWORD%"
"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -c "SELECT version();" > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Nao foi possivel conectar ao banco de dados
    echo [ERRO] Verifique se o PostgreSQL esta rodando
    echo [ERRO] Verifique as credenciais no arquivo .env
    echo [ERRO] Falha ao conectar ao banco >> "%LOG_FILE%" 2>&1
    set "PGPASSWORD="
    pause
    exit /b 1
)
echo [OK] Conexao com banco de dados estabelecida
echo [OK] Conexao estabelecida >> "%LOG_FILE%" 2>&1
echo.

REM ============================================================================
REM BACKUP 1: CUSTOM FORMAT (COMPLETO E COMPRIMIDO)
REM ============================================================================

echo ============================================================================
echo BACKUP 1/3: Custom Format (.dump) - FORMATO PRINCIPAL
echo ============================================================================
echo [INFO] Iniciando backup custom format...
echo [INFO] Arquivo: %BACKUP_FULL%
echo [INFO] Formato: Custom (comprimido, restauravel)
echo [INFO] Incluindo: Schemas, dados, views, funcoes, indices, constraints
echo.
echo [INFO] Iniciando backup custom format >> "%LOG_FILE%" 2>&1

"%PSQL_BIN%\pg_dump.exe" ^
    -U %DB_USER% ^
    -h %DB_HOST% ^
    -p %DB_PORT% ^
    -d %DB_NAME% ^
    -F c ^
    --blobs ^
    --verbose ^
    --no-owner ^
    --no-privileges ^
    -f "%BACKUP_FULL%" >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [ERRO] Falha no backup custom format
    echo [ERRO] Consulte o log: %LOG_FILE%
    echo [ERRO] Falha no backup custom format >> "%LOG_FILE%" 2>&1
    set "PGPASSWORD="
    pause
    exit /b 1
)

REM Verificar se arquivo foi criado e tem tamanho > 0
if not exist "%BACKUP_FULL%" (
    echo [ERRO] Arquivo de backup nao foi criado
    echo [ERRO] Arquivo de backup custom nao criado >> "%LOG_FILE%" 2>&1
    set "PGPASSWORD="
    pause
    exit /b 1
)

for %%A in ("%BACKUP_FULL%") do set "BACKUP_FULL_SIZE=%%~zA"
if %BACKUP_FULL_SIZE% LSS 1024 (
    echo [ERRO] Arquivo de backup muito pequeno: %BACKUP_FULL_SIZE% bytes
    echo [ERRO] Backup custom muito pequeno: %BACKUP_FULL_SIZE% bytes >> "%LOG_FILE%" 2>&1
    set "PGPASSWORD="
    pause
    exit /b 1
)

REM Calcular tamanho em MB
set /a "BACKUP_FULL_SIZE_MB=%BACKUP_FULL_SIZE% / 1048576"
echo [OK] Backup custom format concluido com sucesso
echo [OK] Tamanho: %BACKUP_FULL_SIZE_MB% MB (%BACKUP_FULL_SIZE% bytes)
echo [OK] Backup custom concluido: %BACKUP_FULL_SIZE_MB% MB >> "%LOG_FILE%" 2>&1
echo.

REM ============================================================================
REM BACKUP 2: SQL PLAIN TEXT (LEGÍVEL)
REM ============================================================================

echo ============================================================================
echo BACKUP 2/3: SQL Plain Text (.sql) - FORMATO LEGIVEL
echo ============================================================================
echo [INFO] Iniciando backup SQL plain text...
echo [INFO] Arquivo: %BACKUP_SQL%
echo [INFO] Formato: Plain SQL (legivel, editavel)
echo [INFO] Incluindo: CREATE DATABASE, DROP statements
echo.
echo [INFO] Iniciando backup SQL plain text >> "%LOG_FILE%" 2>&1

"%PSQL_BIN%\pg_dump.exe" ^
    -U %DB_USER% ^
    -h %DB_HOST% ^
    -p %DB_PORT% ^
    -d %DB_NAME% ^
    -F p ^
    --verbose ^
    --no-owner ^
    --no-privileges ^
    --clean ^
    --if-exists ^
    -f "%BACKUP_SQL%" >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [AVISO] Falha no backup SQL plain text
    echo [AVISO] Backup custom ainda esta disponivel
    echo [AVISO] Falha no backup SQL plain text >> "%LOG_FILE%" 2>&1
) else (
    for %%A in ("%BACKUP_SQL%") do set "BACKUP_SQL_SIZE=%%~zA"
    set /a "BACKUP_SQL_SIZE_MB=!BACKUP_SQL_SIZE! / 1048576"
    echo [OK] Backup SQL plain text concluido
    echo [OK] Tamanho: !BACKUP_SQL_SIZE_MB! MB (!BACKUP_SQL_SIZE! bytes)
    echo [OK] Backup SQL concluido: !BACKUP_SQL_SIZE_MB! MB >> "%LOG_FILE%" 2>&1

    REM Comprimir SQL com gzip
    echo.
    echo [INFO] Comprimindo arquivo SQL com gzip...
    where gzip >nul 2>&1
    if not errorlevel 1 (
        gzip -9 -k "%BACKUP_SQL%" 2>> "%LOG_FILE%"
        if not errorlevel 1 (
            for %%B in ("%BACKUP_SQL%.gz") do set "BACKUP_SQL_GZ_SIZE=%%~zB"
            set /a "BACKUP_SQL_GZ_SIZE_MB=!BACKUP_SQL_GZ_SIZE! / 1048576"
            set /a "SAVINGS=100 - (!BACKUP_SQL_GZ_SIZE! * 100 / !BACKUP_SQL_SIZE!)"
            echo [OK] SQL comprimido para .sql.gz
            echo [OK] Tamanho comprimido: !BACKUP_SQL_GZ_SIZE_MB! MB - Economia: !SAVINGS!%%
            echo [OK] SQL.GZ criado: !BACKUP_SQL_GZ_SIZE_MB! MB (economia !SAVINGS!%%) >> "%LOG_FILE%" 2>&1
        ) else (
            echo [AVISO] Falha ao comprimir - mantendo .sql original
            echo [AVISO] Falha ao comprimir SQL >> "%LOG_FILE%" 2>&1
        )
    ) else (
        echo [AVISO] gzip nao encontrado - .sql nao sera comprimido
        echo [AVISO] gzip nao encontrado >> "%LOG_FILE%" 2>&1
    )
)
echo.

REM ============================================================================
REM BACKUP 3: SCHEMA ONLY (ESTRUTURA)
REM ============================================================================

echo ============================================================================
echo BACKUP 3/3: Schema Only (.sql) - APENAS ESTRUTURA
echo ============================================================================
echo [INFO] Iniciando backup schema only...
echo [INFO] Arquivo: %BACKUP_SCHEMA%
echo [INFO] Conteudo: Apenas DDL (sem dados)
echo [INFO] Util para: Recriar estrutura, version control
echo.
echo [INFO] Iniciando backup schema only >> "%LOG_FILE%" 2>&1

"%PSQL_BIN%\pg_dump.exe" ^
    -U %DB_USER% ^
    -h %DB_HOST% ^
    -p %DB_PORT% ^
    -d %DB_NAME% ^
    -F p ^
    --schema-only ^
    --verbose ^
    --no-owner ^
    --no-privileges ^
    -f "%BACKUP_SCHEMA%" >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [AVISO] Falha no backup schema only
    echo [AVISO] Falha no backup schema only >> "%LOG_FILE%" 2>&1
) else (
    for %%A in ("%BACKUP_SCHEMA%") do set "BACKUP_SCHEMA_SIZE=%%~zA"
    set /a "BACKUP_SCHEMA_SIZE_KB=!BACKUP_SCHEMA_SIZE! / 1024"
    echo [OK] Backup schema only concluido
    echo [OK] Tamanho: !BACKUP_SCHEMA_SIZE_KB! KB (!BACKUP_SCHEMA_SIZE! bytes)
    echo [OK] Backup schema concluido: !BACKUP_SCHEMA_SIZE_KB! KB >> "%LOG_FILE%" 2>&1

    REM Comprimir Schema com gzip
    echo.
    echo [INFO] Comprimindo arquivo schema com gzip...
    where gzip >nul 2>&1
    if not errorlevel 1 (
        gzip -9 -k "%BACKUP_SCHEMA%" 2>> "%LOG_FILE%"
        if not errorlevel 1 (
            for %%B in ("%BACKUP_SCHEMA%.gz") do set "BACKUP_SCHEMA_GZ_SIZE=%%~zB"
            set /a "BACKUP_SCHEMA_GZ_SIZE_KB=!BACKUP_SCHEMA_GZ_SIZE! / 1024"
            set /a "SAVINGS_SCHEMA=100 - (!BACKUP_SCHEMA_GZ_SIZE! * 100 / !BACKUP_SCHEMA_SIZE!)"
            echo [OK] Schema comprimido para .sql.gz
            echo [OK] Tamanho comprimido: !BACKUP_SCHEMA_GZ_SIZE_KB! KB - Economia: !SAVINGS_SCHEMA!%%
            echo [OK] Schema.GZ criado: !BACKUP_SCHEMA_GZ_SIZE_KB! KB (economia !SAVINGS_SCHEMA!%%) >> "%LOG_FILE%" 2>&1
        ) else (
            echo [AVISO] Falha ao comprimir schema
            echo [AVISO] Falha ao comprimir schema >> "%LOG_FILE%" 2>&1
        )
    )
)
echo.

REM ============================================================================
REM BACKUP 4: DATA ONLY (APENAS DADOS)
REM ============================================================================

echo ============================================================================
echo BACKUP 4/4: Data Only (.dump) - APENAS DADOS
echo ============================================================================
echo [INFO] Iniciando backup data only...
echo [INFO] Arquivo: %BACKUP_DATA%
echo [INFO] Conteudo: Apenas dados (sem schema)
echo [INFO] Util para: Restauracao seletiva de dados
echo.
echo [INFO] Iniciando backup data only >> "%LOG_FILE%" 2>&1

"%PSQL_BIN%\pg_dump.exe" ^
    -U %DB_USER% ^
    -h %DB_HOST% ^
    -p %DB_PORT% ^
    -d %DB_NAME% ^
    -F c ^
    --data-only ^
    --verbose ^
    --no-owner ^
    --no-privileges ^
    -f "%BACKUP_DATA%" >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [AVISO] Falha no backup data only
    echo [AVISO] Falha no backup data only >> "%LOG_FILE%" 2>&1
) else (
    for %%A in ("%BACKUP_DATA%") do set "BACKUP_DATA_SIZE=%%~zA"
    set /a "BACKUP_DATA_SIZE_MB=!BACKUP_DATA_SIZE! / 1048576"
    echo [OK] Backup data only concluido
    echo [OK] Tamanho: !BACKUP_DATA_SIZE_MB! MB (!BACKUP_DATA_SIZE! bytes)
    echo [OK] Backup data concluido: !BACKUP_DATA_SIZE_MB! MB >> "%LOG_FILE%" 2>&1
)
echo.

REM ============================================================================
REM CRIAR LINK SIMBÓLICO PARA LATEST
REM ============================================================================

echo [INFO] Atualizando link para ultimo backup...
copy /Y "%BACKUP_FULL%" "%BACKUP_ROOT%\latest\inhire_latest.dump" > nul 2>&1
if not errorlevel 1 (
    echo [OK] Link para ultimo backup atualizado
    echo [OK] Link para latest atualizado >> "%LOG_FILE%" 2>&1
)
echo.

REM ============================================================================
REM ESTATÍSTICAS DO BANCO
REM ============================================================================

echo ============================================================================
echo ESTATISTICAS DO BANCO DE DADOS
echo ============================================================================
echo [INFO] Coletando estatisticas...
echo.

echo [ESTATISTICAS] >> "%LOG_FILE%" 2>&1
"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -c "SELECT 'Tabelas' as tipo, COUNT(*) as quantidade FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' UNION ALL SELECT 'Views', COUNT(*) FROM information_schema.views WHERE table_schema = 'public' UNION ALL SELECT 'Funcoes', COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public';" >> "%LOG_FILE%" 2>&1

"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -c "SELECT tablename, pg_size_pretty(pg_total_relation_size('public.'||tablename)) as tamanho FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size('public.'||tablename) DESC LIMIT 10;" >> "%LOG_FILE%" 2>&1

echo [OK] Estatisticas coletadas (ver log)
echo.

REM ============================================================================
REM RESUMO FINAL
REM ============================================================================

echo ============================================================================
echo RESUMO DO BACKUP
echo ============================================================================
echo.
echo [OK] Backup concluido com sucesso!
echo.
echo Arquivos criados:
echo.
echo   1. Custom format (PRINCIPAL):
echo      %BACKUP_FULL%
echo      Tamanho: %BACKUP_FULL_SIZE_MB% MB
echo.
if exist "%BACKUP_SQL%" (
    echo   2. SQL plain text:
    echo      %BACKUP_SQL%
    echo      Tamanho: %BACKUP_SQL_SIZE_MB% MB
    if exist "%BACKUP_SQL%.gz" (
        echo      Comprimido: %BACKUP_SQL%.gz
        echo      Tamanho GZ: %BACKUP_SQL_GZ_SIZE_MB% MB (economia %SAVINGS%%%)
    )
    echo.
)
if exist "%BACKUP_SCHEMA%" (
    echo   3. Schema only:
    echo      %BACKUP_SCHEMA%
    echo      Tamanho: %BACKUP_SCHEMA_SIZE_KB% KB
    if exist "%BACKUP_SCHEMA%.gz" (
        echo      Comprimido: %BACKUP_SCHEMA%.gz
        echo      Tamanho GZ: %BACKUP_SCHEMA_GZ_SIZE_KB% KB (economia %SAVINGS_SCHEMA%%%)
    )
    echo.
)
if exist "%BACKUP_DATA%" (
    echo   4. Data only:
    echo      %BACKUP_DATA%
    echo      Tamanho: %BACKUP_DATA_SIZE_MB% MB
    echo.
)
echo   Log detalhado:
echo      %LOG_FILE%
echo.
echo ============================================================================
echo PROXIMOS PASSOS
echo ============================================================================
echo.
echo 1. VALIDAR BACKUP:
echo    psql -U postgres -d inhire -f scripts\backup\validate_backup.sql
echo.
echo 2. RESTAURAR (se necessario):
echo    scripts\backup\restore_inhire_windows.bat
echo.
echo 3. AGENDAR BACKUPS AUTOMATICOS:
echo    Ver documentacao em docs\guides\GUIA_BACKUP_RESTORE.md
echo.
echo ============================================================================
echo.

REM Limpar variável de senha
set "PGPASSWORD="

echo [INFO] Backup finalizado >> "%LOG_FILE%" 2>&1
echo Pressione qualquer tecla para sair...
pause > nul
