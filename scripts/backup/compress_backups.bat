@echo off
REM ============================================================================
REM Script de Compressão de Backups - Banco de Dados Inhire
REM ============================================================================
REM Autor: Auto-gerado
REM Data: 2026-03-23
REM Descrição: Comprime arquivos SQL usando gzip
REM ============================================================================

setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0..\.."
set "BACKUP_ROOT=%PROJECT_ROOT%\Backup_BD_Inhire"

echo ============================================================================
echo COMPRESSAO DE ARQUIVOS DE BACKUP
echo ============================================================================
echo.
echo Este script comprime arquivos .sql para .sql.gz usando gzip
echo.
echo Pastas processadas:
echo   - %BACKUP_ROOT%\sql\
echo   - %BACKUP_ROOT%\schema\
echo.
echo ============================================================================
echo.

set "GZIP_CMD=gzip"

REM Verificar se gzip está disponível
where gzip >nul 2>&1
if errorlevel 1 (
    echo [ERRO] gzip nao encontrado no PATH
    echo [INFO] Instale o Git for Windows ou adicione gzip ao PATH
    echo [INFO] Download: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] gzip encontrado
echo.

REM ============================================================================
REM COMPRIMIR ARQUIVOS SQL
REM ============================================================================

echo ============================================================================
echo COMPRIMINDO ARQUIVOS SQL
echo ============================================================================
echo.

set "COMPRESSED_COUNT=0"
set "SKIPPED_COUNT=0"
set "ERROR_COUNT=0"

REM Processar pasta sql/
echo [INFO] Processando pasta sql\...
if exist "%BACKUP_ROOT%\sql\*.sql" (
    for %%F in ("%BACKUP_ROOT%\sql\*.sql") do (
        set "SQL_FILE=%%F"
        set "GZ_FILE=%%F.gz"

        REM Verificar se já existe .gz
        if exist "!GZ_FILE!" (
            echo [SKIP] %%~nxF - ja comprimido
            set /a "SKIPPED_COUNT+=1"
        ) else (
            echo [INFO] Comprimindo %%~nxF...
            gzip -9 -k "!SQL_FILE!" 2>nul

            if errorlevel 1 (
                echo [ERRO] Falha ao comprimir %%~nxF
                set /a "ERROR_COUNT+=1"
            ) else (
                echo [OK] %%~nxF.gz criado

                REM Comparar tamanhos
                for %%A in ("!SQL_FILE!") do set "SIZE_ORIG=%%~zA"
                for %%B in ("!GZ_FILE!") do set "SIZE_COMP=%%~zB"

                set /a "SIZE_ORIG_MB=!SIZE_ORIG! / 1048576"
                set /a "SIZE_COMP_MB=!SIZE_COMP! / 1048576"
                set /a "SAVINGS=100 - (!SIZE_COMP! * 100 / !SIZE_ORIG!)"

                echo [INFO] Original: !SIZE_ORIG_MB! MB, Comprimido: !SIZE_COMP_MB! MB, Economia: !SAVINGS!%%

                set /a "COMPRESSED_COUNT+=1"

                REM Opcional: Remover .sql original (comentado por segurança)
                REM del "!SQL_FILE!"
                REM echo [INFO] Original removido
            )
        )
        echo.
    )
) else (
    echo [INFO] Nenhum arquivo .sql encontrado
)

echo.

REM Processar pasta schema/
echo [INFO] Processando pasta schema\...
if exist "%BACKUP_ROOT%\schema\*.sql" (
    for %%F in ("%BACKUP_ROOT%\schema\*.sql") do (
        set "SQL_FILE=%%F"
        set "GZ_FILE=%%F.gz"

        if exist "!GZ_FILE!" (
            echo [SKIP] %%~nxF - ja comprimido
            set /a "SKIPPED_COUNT+=1"
        ) else (
            echo [INFO] Comprimindo %%~nxF...
            gzip -9 -k "!SQL_FILE!" 2>nul

            if errorlevel 1 (
                echo [ERRO] Falha ao comprimir %%~nxF
                set /a "ERROR_COUNT+=1"
            ) else (
                echo [OK] %%~nxF.gz criado

                for %%A in ("!SQL_FILE!") do set "SIZE_ORIG=%%~zA"
                for %%B in ("!GZ_FILE!") do set "SIZE_COMP=%%~zB"

                set /a "SIZE_ORIG_KB=!SIZE_ORIG! / 1024"
                set /a "SIZE_COMP_KB=!SIZE_COMP! / 1024"
                set /a "SAVINGS=100 - (!SIZE_COMP! * 100 / !SIZE_ORIG!)"

                echo [INFO] Original: !SIZE_ORIG_KB! KB, Comprimido: !SIZE_COMP_KB! KB, Economia: !SAVINGS!%%

                set /a "COMPRESSED_COUNT+=1"
            )
        )
        echo.
    )
) else (
    echo [INFO] Nenhum arquivo .sql encontrado
)

echo.

REM ============================================================================
REM RESUMO
REM ============================================================================

echo ============================================================================
echo RESUMO DA COMPRESSAO
echo ============================================================================
echo.
echo Arquivos comprimidos: %COMPRESSED_COUNT%
echo Arquivos pulados:     %SKIPPED_COUNT%
echo Erros:                %ERROR_COUNT%
echo.
echo ============================================================================
echo.

if %COMPRESSED_COUNT% GTR 0 (
    echo [OK] Compressao concluida com sucesso!
    echo.
    echo [INFO] Para remover arquivos .sql originais e manter apenas .gz:
    echo        Edite este script e descomente a linha "del SQL_FILE"
    echo.
) else (
    echo [INFO] Nenhum arquivo foi comprimido
    echo [INFO] Todos os arquivos SQL ja estao comprimidos (.sql.gz)
    echo.
)

echo ============================================================================
echo.
pause
