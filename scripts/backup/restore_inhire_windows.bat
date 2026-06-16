@echo off
REM ============================================================================
REM Script de Restauração - Banco de Dados Inhire
REM ============================================================================
REM Autor: Auto-gerado
REM Data: 2026-03-23
REM Descrição: Restauração do PostgreSQL database 'inhire' a partir de backup
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

echo ============================================================================
echo RESTAURACAO DO BANCO DE DADOS INHIRE
echo ============================================================================
echo.
echo [AVISO] Este script ira SOBRESCREVER o banco de dados atual!
echo [AVISO] Certifique-se de que voce tem um backup antes de continuar.
echo.
echo Database: %DB_NAME%
echo Host: %DB_HOST%:%DB_PORT%
echo Usuario: %DB_USER%
echo.
echo ============================================================================
echo.

REM ============================================================================
REM VALIDAÇÕES PRÉ-EXECUÇÃO
REM ============================================================================

echo [INFO] Validando pre-requisitos...

REM Verificar se pg_restore existe
if not exist "%PSQL_BIN%\pg_restore.exe" (
    echo [ERRO] pg_restore.exe nao encontrado em: %PSQL_BIN%
    echo [ERRO] Verifique a instalacao do PostgreSQL
    pause
    exit /b 1
)
echo [OK] pg_restore.exe encontrado

REM Verificar se arquivo .env existe
if not exist "%ENV_FILE%" (
    echo [ERRO] Arquivo .env nao encontrado em: %ENV_FILE%
    echo [ERRO] Arquivo necessario para obter credenciais do banco
    pause
    exit /b 1
)
echo [OK] Arquivo .env encontrado

REM Ler senha do arquivo .env
for /f "usebackq tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
    if "%%a"=="DB_PASSWORD" set "DB_PASSWORD=%%b"
)

if "%DB_PASSWORD%"=="" (
    echo [ERRO] DB_PASSWORD nao encontrada no arquivo .env
    pause
    exit /b 1
)
echo [OK] Credenciais carregadas
echo.

REM ============================================================================
REM SELEÇÃO DO ARQUIVO DE BACKUP
REM ============================================================================

echo ============================================================================
echo SELECIONE O TIPO DE RESTAURACAO
echo ============================================================================
echo.
echo 1. Restaurar do backup mais recente (latest)
echo 2. Restaurar de arquivo custom format (.dump)
echo 3. Restaurar de arquivo SQL plain text (.sql)
echo 4. Restaurar de arquivo SQL comprimido (.sql.gz)
echo 5. Restaurar apenas dados (data-only .dump)
echo 6. Listar backups disponiveis
echo 7. Cancelar
echo.
set /p "OPCAO=Digite sua opcao (1-7): "

if "%OPCAO%"=="7" (
    echo [INFO] Operacao cancelada pelo usuario
    pause
    exit /b 0
)

if "%OPCAO%"=="6" (
    echo.
    echo ============================================================================
    echo BACKUPS DISPONIVEIS
    echo ============================================================================
    echo.
    echo [CUSTOM FORMAT - .dump]
    dir /B /O-D "%BACKUP_ROOT%\full\*.dump" 2>nul
    echo.
    echo [SQL PLAIN TEXT - .sql]
    dir /B /O-D "%BACKUP_ROOT%\sql\*.sql" 2>nul
    echo.
    echo [SQL COMPRIMIDO - .sql.gz]
    dir /B /O-D "%BACKUP_ROOT%\sql\*.sql.gz" 2>nul
    echo.
    echo [DATA ONLY - .dump]
    dir /B /O-D "%BACKUP_ROOT%\data\*.dump" 2>nul
    echo.
    echo [LATEST]
    dir /B "%BACKUP_ROOT%\latest\*.dump" 2>nul
    echo.
    echo ============================================================================
    pause
    goto :EOF
)

set "BACKUP_FILE="
set "RESTORE_TYPE="

if "%OPCAO%"=="1" (
    set "BACKUP_FILE=%BACKUP_ROOT%\latest\inhire_latest.dump"
    set "RESTORE_TYPE=custom"
    echo [INFO] Usando backup mais recente
) else if "%OPCAO%"=="2" (
    echo.
    echo Arquivos disponiveis:
    dir /B /O-D "%BACKUP_ROOT%\full\*.dump" 2>nul
    echo.
    set /p "BACKUP_FILENAME=Digite o nome do arquivo (sem caminho): "
    set "BACKUP_FILE=%BACKUP_ROOT%\full\!BACKUP_FILENAME!"
    set "RESTORE_TYPE=custom"
) else if "%OPCAO%"=="3" (
    echo.
    echo Arquivos disponiveis:
    dir /B /O-D "%BACKUP_ROOT%\sql\*.sql" 2>nul
    echo.
    set /p "BACKUP_FILENAME=Digite o nome do arquivo (sem caminho): "
    set "BACKUP_FILE=%BACKUP_ROOT%\sql\!BACKUP_FILENAME!"
    set "RESTORE_TYPE=sql"
) else if "%OPCAO%"=="4" (
    echo.
    echo Arquivos disponiveis:
    dir /B /O-D "%BACKUP_ROOT%\sql\*.sql.gz" 2>nul
    echo.
    set /p "BACKUP_FILENAME=Digite o nome do arquivo (sem caminho): "
    set "BACKUP_FILE=%BACKUP_ROOT%\sql\!BACKUP_FILENAME!"
    set "RESTORE_TYPE=sqlgz"
) else if "%OPCAO%"=="5" (
    echo.
    echo Arquivos disponiveis:
    dir /B /O-D "%BACKUP_ROOT%\data\*.dump" 2>nul
    echo.
    set /p "BACKUP_FILENAME=Digite o nome do arquivo (sem caminho): "
    set "BACKUP_FILE=%BACKUP_ROOT%\data\!BACKUP_FILENAME!"
    set "RESTORE_TYPE=dataonly"
) else (
    echo [ERRO] Opcao invalida
    pause
    exit /b 1
)

REM Verificar se arquivo existe
if not exist "%BACKUP_FILE%" (
    echo [ERRO] Arquivo de backup nao encontrado: %BACKUP_FILE%
    pause
    exit /b 1
)

echo [OK] Arquivo de backup encontrado: %BACKUP_FILE%
for %%A in ("%BACKUP_FILE%") do set "BACKUP_SIZE=%%~zA"
set /a "BACKUP_SIZE_MB=%BACKUP_SIZE% / 1048576"
echo [INFO] Tamanho do arquivo: %BACKUP_SIZE_MB% MB
echo.

REM ============================================================================
REM CONFIRMAÇÃO FINAL
REM ============================================================================

echo ============================================================================
echo CONFIRMACAO FINAL
echo ============================================================================
echo.
echo [AVISO CRITICO] Esta operacao ira:
echo   1. APAGAR todos os dados atuais do banco '%DB_NAME%'
echo   2. RESTAURAR os dados do backup selecionado
echo   3. Esta acao NAO PODE SER DESFEITA
echo.
echo Arquivo de backup: %BACKUP_FILE%
echo Tamanho: %BACKUP_SIZE_MB% MB
echo.
set /p "CONFIRMA=Tem certeza que deseja continuar? (S/N): "

if /i not "%CONFIRMA%"=="S" (
    echo [INFO] Operacao cancelada pelo usuario
    pause
    exit /b 0
)

echo.
echo [INFO] Iniciando restauracao...
echo.

REM ============================================================================
REM TESTAR CONEXÃO
REM ============================================================================

echo [INFO] Testando conexao com o banco...
set "PGPASSWORD=%DB_PASSWORD%"
"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d postgres -c "SELECT version();" > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Nao foi possivel conectar ao banco de dados
    echo [ERRO] Verifique se o PostgreSQL esta rodando
    set "PGPASSWORD="
    pause
    exit /b 1
)
echo [OK] Conexao estabelecida
echo.

REM ============================================================================
REM DROPAR E RECRIAR BANCO (se necessário)
REM ============================================================================

echo ============================================================================
echo ETAPA 1/3: PREPARACAO DO BANCO
echo ============================================================================
echo.
echo [INFO] Encerrando conexoes ativas...

"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '%DB_NAME%' AND pid <> pg_backend_pid();" > nul 2>&1

echo [OK] Conexoes encerradas
echo.

REM ============================================================================
REM RESTAURAÇÃO
REM ============================================================================

echo ============================================================================
echo ETAPA 2/3: RESTAURACAO DOS DADOS
echo ============================================================================
echo.

if "%RESTORE_TYPE%"=="custom" (
    echo [INFO] Restaurando do formato custom (.dump)...
    echo [INFO] Isso pode levar alguns minutos...
    echo.

    "%PSQL_BIN%\pg_restore.exe" ^
        -U %DB_USER% ^
        -h %DB_HOST% ^
        -p %DB_PORT% ^
        -d %DB_NAME% ^
        --verbose ^
        --clean ^
        --if-exists ^
        --no-owner ^
        --no-privileges ^
        "%BACKUP_FILE%"

    if errorlevel 1 (
        echo.
        echo [AVISO] pg_restore reportou alguns avisos
        echo [INFO] Isso e normal - alguns objetos podem ja existir
        echo [INFO] Verifique se a restauracao foi bem-sucedida
    ) else (
        echo.
        echo [OK] Restauracao custom format concluida
    )

) else if "%RESTORE_TYPE%"=="sql" (
    echo [INFO] Restaurando do formato SQL (.sql)...
    echo [INFO] Isso pode levar alguns minutos...
    echo.

    "%PSQL_BIN%\psql.exe" ^
        -U %DB_USER% ^
        -h %DB_HOST% ^
        -p %DB_PORT% ^
        -d %DB_NAME% ^
        -f "%BACKUP_FILE%"

    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao restaurar do SQL
        set "PGPASSWORD="
        pause
        exit /b 1
    ) else (
        echo.
        echo [OK] Restauracao SQL concluida
    )

) else if "%RESTORE_TYPE%"=="sqlgz" (
    echo [INFO] Restaurando do formato SQL comprimido (.sql.gz)...
    echo [INFO] Descomprimindo arquivo...
    echo.

    REM Verificar gzip
    where gzip >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] gzip nao encontrado - instale Git for Windows
        set "PGPASSWORD="
        pause
        exit /b 1
    )

    REM Criar arquivo temporário
    set "TEMP_SQL=%TEMP%\inhire_restore_temp.sql"
    gzip -d -c "%BACKUP_FILE%" > "%TEMP_SQL%" 2>nul

    if errorlevel 1 (
        echo [ERRO] Falha ao descomprimir arquivo
        set "PGPASSWORD="
        pause
        exit /b 1
    )

    echo [OK] Arquivo descomprimido
    echo [INFO] Restaurando dados (pode levar varios minutos)...
    echo.

    "%PSQL_BIN%\psql.exe" ^
        -U %DB_USER% ^
        -h %DB_HOST% ^
        -p %DB_PORT% ^
        -d %DB_NAME% ^
        -f "%TEMP_SQL%"

    REM Limpar arquivo temporário
    del "%TEMP_SQL%" 2>nul

    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao restaurar do SQL.GZ
        set "PGPASSWORD="
        pause
        exit /b 1
    ) else (
        echo.
        echo [OK] Restauracao SQL.GZ concluida
    )

) else if "%RESTORE_TYPE%"=="dataonly" (
    echo [INFO] Restaurando apenas dados (data-only .dump)...
    echo [INFO] Schema existente sera mantido
    echo [INFO] Isso pode levar alguns minutos...
    echo.

    "%PSQL_BIN%\pg_restore.exe" ^
        -U %DB_USER% ^
        -h %DB_HOST% ^
        -p %DB_PORT% ^
        -d %DB_NAME% ^
        --verbose ^
        --data-only ^
        --no-owner ^
        --no-privileges ^
        "%BACKUP_FILE%"

    if errorlevel 1 (
        echo.
        echo [AVISO] pg_restore reportou alguns avisos
        echo [INFO] Verifique se a restauracao foi bem-sucedida
    ) else (
        echo.
        echo [OK] Restauracao data-only concluida
    )
)

echo.

REM ============================================================================
REM VALIDAÇÃO PÓS-RESTAURAÇÃO
REM ============================================================================

echo ============================================================================
echo ETAPA 3/3: VALIDACAO POS-RESTAURACAO
echo ============================================================================
echo.
echo [INFO] Executando validacoes basicas...
echo.

REM Contar tabelas
for /f "tokens=*" %%A in ('"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -t -A -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"') do set "TABLE_COUNT=%%A"
echo [INFO] Tabelas encontradas: %TABLE_COUNT%

REM Contar views
for /f "tokens=*" %%A in ('"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -t -A -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public';"') do set "VIEW_COUNT=%%A"
echo [INFO] Views encontradas: %VIEW_COUNT%

REM Contar funções
for /f "tokens=*" %%A in ('"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -t -A -c "SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public';"') do set "FUNC_COUNT=%%A"
echo [INFO] Funcoes encontradas: %FUNC_COUNT%

echo.
echo [INFO] Contando registros nas tabelas principais...
echo.

"%PSQL_BIN%\psql.exe" -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -c "SELECT 'vagas' as tabela, COUNT(*) as registros FROM vagas UNION ALL SELECT 'posicoes', COUNT(*) FROM posicoes UNION ALL SELECT 'candidaturas', COUNT(*) FROM candidaturas UNION ALL SELECT 'talentos', COUNT(*) FROM talentos ORDER BY tabela;"

echo.

REM ============================================================================
REM RESUMO FINAL
REM ============================================================================

echo ============================================================================
echo RESUMO DA RESTAURACAO
echo ============================================================================
echo.
echo [OK] Restauracao concluida!
echo.
echo Estatisticas:
echo   - Tabelas: %TABLE_COUNT%
echo   - Views: %VIEW_COUNT%
echo   - Funcoes: %FUNC_COUNT%
echo.
echo Arquivo restaurado: %BACKUP_FILE%
echo.
echo ============================================================================
echo PROXIMOS PASSOS
echo ============================================================================
echo.
echo 1. VALIDAR DADOS:
echo    psql -U postgres -d inhire -f scripts\backup\validate_backup.sql
echo.
echo 2. TESTAR APLICACAO:
echo    Verifique se a aplicacao esta funcionando corretamente
echo.
echo 3. TESTAR VIEWS:
echo    psql -U postgres -d inhire -c "SELECT COUNT(*) FROM vw_analise_posicoes;"
echo.
echo ============================================================================
echo.

REM Limpar variável de senha
set "PGPASSWORD="

echo Pressione qualquer tecla para sair...
pause > nul
