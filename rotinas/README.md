# Rotinas Agendadas Inhire

Scripts .BAT para execução automática via Windows Task Scheduler.

## 📁 Arquivos

### Rotinas Mestras

**`rotina_diaria.bat`**
- **Frequência:** Segunda a Sábado, 08:00 e 20:00
- **Duração:** ~50 minutos
- **Executa:**
  1. Sync Incremental (~45 min)
  2. Export Sheets Principal
  3. Export Análise Posições
  4. Export Dados Jade
  5. Export Candidaturas

**`rotina_semanal.bat`**
- **Frequência:** Domingo 02:00
- **Duração:** ~70 minutos
- **Executa:**
  1. Backup BD (~10 min)
  2. Sync FULL (~55 min)
  3. Export Sheets (~5 min)

---

### Rotinas de Sincronização

**`sync_full.bat`**
- Sincronização completa (55 min)
- 100% dos dados da API Inhire
- Executar 1x/semana

**`sync_incremental.bat`**
- Sincronização incremental (40-50 min)
- Apenas dados modificados
- Executar 2x/dia

---

### Rotinas de Exportação

**`export_sheets.bat`**
- Exporta views principais para Google Sheets
- Duração: ~15 segundos

**`export_analise_posicoes.bat`**
- Exporta vw_analise_posicoes (1.383 registros)
- Duração: ~10 segundos

**`export_candidaturas.bat`**
- Exporta vw_relatorio_candidaturas (35k+ registros)
- Duração: ~15 segundos
- Envia notificação via Google Chat webhook

**`export_dados_jade.bat`**
- Exporta vw_dados_jade (dados customizados)
- Duração: ~10 segundos

**`export_funil.bat`**
- Exporta vw_funil_performance (85k+ registros)
- Duração: ~30 segundos
- Executar 1x/semana

---

### Rotinas de Manutenção

**`backup_bd.bat`**
- Backup completo do PostgreSQL
- Duração: ~10 minutos
- Executar 1x/semana (Domingo 02:00)

**`health_check.bat`**
- Verifica saúde do sistema
- Duração: ~5 segundos
- Executar diariamente

---

## 📅 Agenda Recomendada

### Domingo
```
02:00 - rotina_semanal.bat (Backup + Sync FULL + Export)
```

### Segunda a Sábado
```
08:00 - rotina_diaria.bat (Sync Incremental + Exports)
20:00 - rotina_diaria.bat (Sync Incremental + Exports)
```

### Opcional
```
Diário 06:00 - health_check.bat
Sábado 23:00 - export_funil.bat (semanal)
```

---

## ⚙️ Configuração no Windows Task Scheduler

### Passo a Passo

1. Abrir "Agendador de Tarefas" (Task Scheduler)

2. Criar Nova Tarefa:
   - Ação → Criar Tarefa Básica
   - Nome: "Inhire - Rotina Diária"
   - Gatilho: Diário às 08:00
   - Ação: Iniciar um programa
   - Programa: `C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\rotina_diaria.bat`

3. Configurações Avançadas:
   - Executar estando o usuário conectado ou não: ✅
   - Executar com privilégios mais altos: ✅
   - Configurar para: Windows 10

4. Repetir para:
   - Rotina Diária 20:00
   - Rotina Semanal (Domingo 02:00)

### Testar Execução

```bash
# Testar rotina manualmente
cd "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
rotinas\rotina_diaria.bat
```

---

## 📊 Monitoramento

### Logs

Todos os scripts gravam em:
- `logs\rotinas.log` - Log principal consolidado
- `logs\export_*.log` - Logs de exportação específicos
- `logs\inhire_sync.log` - Log de sincronização

### Verificar Execução

```bash
# Ver últimas execuções
tail -f logs\rotinas.log

# Ver erros recentes
grep "ERRO" logs\rotinas.log
```

---

## 🔧 Troubleshooting

### Rotina não executou

1. Verificar Task Scheduler:
   - Tarefa está habilitada?
   - Última execução teve erro?
   - Verificar log do Task Scheduler

2. Verificar logs:
   ```bash
   type logs\rotinas.log
   ```

3. Testar manualmente:
   ```bash
   rotinas\rotina_diaria.bat
   ```

### Erro "Python não encontrado"

- Verificar que Python está no PATH
- Ou usar caminho completo no .bat:
  ```batch
  C:\Python\python.exe scripts\export\export_sheets.py
  ```

### Erro "psql não encontrado"

- PostgreSQL bin não está no PATH
- Scripts já usam caminho completo:
  ```batch
  "C:\Program Files\PostgreSQL\18\bin\psql.exe"
  ```

---

## 📝 Criação de Nova Rotina

Template para criar nova rotina .BAT:

```batch
@echo off
REM ============================================================================
REM NOME DA ROTINA - Descrição breve
REM Duração: ~XX minutos
REM Frequência: Quando executar
REM ============================================================================

cd /d "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

echo ============================================================================
echo NOME DA ROTINA - %date% %time%
echo ============================================================================
echo [%date% %time%] Iniciando NOME DA ROTINA >> logs\rotinas.log

REM Executar comando
python scripts/meu_script.py >> logs\minha_rotina.log 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERRO: NOME DA ROTINA falhou! >> logs\rotinas.log
    echo ERRO: NOME DA ROTINA falhou!
    exit /b 1
) else (
    echo [%date% %time%] NOME DA ROTINA concluído com sucesso >> logs\rotinas.log
    echo NOME DA ROTINA concluído com sucesso
)
```

---

**Última atualização:** 2026-08-21
**Total de rotinas:** 11 scripts .BAT
