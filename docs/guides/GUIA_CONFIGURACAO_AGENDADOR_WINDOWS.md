# Guia Prático: Configurar Agendador de Tarefas do Windows

**Data:** 2026-08-20
**Versão:** 1.0
**Tempo de Configuração:** 20-30 minutos

---

## 📋 O Que Você Tem Pronto

### ✅ Documentação
- `ROTINAS_AGENDAMENTO.md` - Documentação técnica completa (928 linhas)

### ✅ Scripts .BAT (11 arquivos em `rotinas/`)
1. `rotina_diaria.bat` - **MASTER DIÁRIO** (sync + exports automáticos)
2. `rotina_semanal.bat` - **MASTER SEMANAL** (backup + sync full)
3. `sync_full.bat` - Sync completa semanal
4. `sync_incremental.bat` - Sync incremental 2x/dia
5. `backup_bd.bat` - Backup diário
6. `health_check.bat` - Verificação de saúde
7. `export_sheets.bat` - Export principal
8. `export_analise_posicoes.bat` - Export análise
9. `export_funil.bat` - Export funil semanal
10. `export_dados_jade.bat` - Export Jade
11. `export_candidaturas.bat` - Export candidaturas

---

## 🚀 Configuração Rápida (6 Tarefas Essenciais)

### Passo 1: Abrir Agendador de Tarefas

```
1. Pressione Win + R
2. Digite: taskschd.msc
3. Pressione Enter
```

### Passo 2: Criar Pasta de Organização (Opcional mas Recomendado)

```
1. No painel esquerdo, clique com botão direito em "Biblioteca do Agendador de Tarefas"
2. Selecione "Nova Pasta"
3. Nome: "Inhire"
4. Clique em OK
```

---

## 📝 Tarefas Essenciais (Copiar e Colar)

### ⭐ TAREFA 1: Backup Diário (CRÍTICA)

**Nome:** `Inhire - Backup BD Diário`

**Descrição:**
```
Backup completo do banco de dados PostgreSQL antes de qualquer sincronização
```

**Gatilho:**
- Tipo: Diário
- Início: Hoje (data atual)
- Horário: 01:00
- Recorrer a cada: 1 dia

**Ação:**
- Programa/script:
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\backup_bd.bat
```
- Iniciar em:
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire
```

**Configurações Avançadas:**
- ☑ Executar com privilégios mais altos
- ☑ Executar independentemente de o usuário estar conectado
- Configurar para: Windows 10

---

### ⭐ TAREFA 2: Health Check Diário

**Nome:** `Inhire - Health Check Diário`

**Descrição:**
```
Verificação de saúde do sistema (API, BD, logs)
```

**Gatilho:**
- Tipo: Diário
- Horário: 06:00

**Ação:**
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\health_check.bat
```

**Configurações:**
- ☑ Executar com privilégios mais altos
- Tempo limite: 10 minutos

---

### ⭐ TAREFA 3: Rotina Diária Manhã (CRÍTICA)

**Nome:** `Inhire - Rotina Diária Manhã`

**Descrição:**
```
Sync incremental + 4 exports (vw_analise_posicoes, sheets, jade, candidaturas)
Duração: ~50 minutos
```

**Gatilho:**
- Tipo: Semanal
- Dias: Segunda, Terça, Quarta, Quinta, Sexta, Sábado
- Horário: 08:00

**Ação:**
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\rotina_diaria.bat
```

**Configurações:**
- ☑ Executar com privilégios mais altos
- ☑ Executar independentemente de o usuário estar conectado
- Tempo limite: 2 horas

---

### ⭐ TAREFA 4: Sync Incremental Noite

**Nome:** `Inhire - Sync Incremental Noite`

**Descrição:**
```
Sync incremental noturno + export sheets
Duração: ~45 minutos
```

**Gatilho:**
- Tipo: Semanal
- Dias: Segunda, Terça, Quarta, Quinta, Sexta, Sábado
- Horário: 20:00

**Ação:**
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\sync_incremental.bat
```

**Ação Adicional (Encadeada):**
- Criar outra ação para executar após:
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\export_sheets.bat
```

**Configurações:**
- ☑ Executar com privilégios mais altos
- Tempo limite: 2 horas

---

### ⭐ TAREFA 5: Rotina Semanal Domingo (CRÍTICA)

**Nome:** `Inhire - Rotina Semanal Domingo`

**Descrição:**
```
Backup + Sync FULL + Export
Duração: ~70 minutos (10 min backup + 55 min sync + 5 min export)
```

**Gatilho:**
- Tipo: Semanal
- Dia: Domingo
- Horário: 02:00

**Ação:**
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\rotina_semanal.bat
```

**Configurações:**
- ☑ Executar com privilégios mais altos
- ☑ Executar independentemente de o usuário estar conectado
- Tempo limite: 3 horas

---

### ⭐ TAREFA 6: Export Funil Performance Semanal (Opcional)

**Nome:** `Inhire - Export Funil Semanal`

**Descrição:**
```
Exportação semanal da view vw_funil_performance (~85k registros)
```

**Gatilho:**
- Tipo: Semanal
- Dia: Segunda-feira
- Horário: 09:00

**Ação:**
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\rotinas\export_funil.bat
```

**Configurações:**
- ☑ Executar com privilégios mais altos
- Tempo limite: 10 minutos

---

## 📅 Calendário Semanal Configurado

```
DOMINGO
├── 01:00 - Backup BD (~10 min)
└── 02:00 - Rotina Semanal: Backup + Sync FULL + Export (~70 min)

SEGUNDA a SÁBADO
├── 01:00 - Backup BD (~10 min)
├── 06:00 - Health Check (~1 min)
├── 08:00 - Rotina Diária: Sync Incremental + 4 Exports (~50 min)
└── 20:00 - Sync Incremental + Export Sheets (~45 min)

SEGUNDA (adicional)
└── 09:00 - Export Funil Performance (~20 seg)
```

---

## 🔧 Configurações Importantes

### Para TODAS as Tarefas:

**Aba "Geral":**
- ☑ Executar com privilégios mais altos
- ☑ Executar independentemente de o usuário estar conectado
- Configurar para: Windows 10

**Aba "Gatilhos":**
- ☑ Habilitado
- Interromper tarefa se for executada por: (configurar timeout conforme tabela abaixo)

**Aba "Ações":**
- Programa/script: Caminho completo do .bat
- Iniciar em: `C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire`

**Aba "Condições":**
- ☐ Iniciar a tarefa somente se o computador estiver ocioso
- ☑ Iniciar a tarefa somente se o computador estiver utilizando energia CA (se for desktop)
- ☐ Interromper se o computador alternar para energia de bateria

**Aba "Configurações":**
- ☑ Permitir que a tarefa seja executada sob demanda
- ☑ Executar a tarefa assim que possível após perder um início agendado
- ☑ Se a tarefa falhar, reiniciar a cada: 10 minutos (opcional)
- Tentar reiniciar até: 3 vezes
- Interromper a tarefa se for executada por: (ver tabela)
- ☑ Se a tarefa já estiver em execução, a seguinte regra se aplicará: Não iniciar uma nova instância

### Timeouts Recomendados

| Tarefa | Timeout | Justificativa |
|--------|---------|---------------|
| Backup BD | 30 min | Backup pode demorar com BD grande |
| Health Check | 10 min | Rápido, 1 min normal |
| Rotina Diária | 2 horas | Sync 45 min + exports |
| Sync Incremental Noite | 2 horas | Sync pode demorar |
| Rotina Semanal | 3 horas | Sync FULL 55 min + margem |
| Export Funil | 10 min | Rápido, 20 seg normal |

---

## 🧪 Testar Configuração

### Teste Manual de Cada Script

Antes de agendar, teste manualmente cada .bat:

```batch
REM 1. Abrir CMD como Administrador
REM 2. Navegar para pasta
cd "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"

REM 3. Testar backup (mais rápido)
rotinas\backup_bd.bat

REM 4. Testar health check
rotinas\health_check.bat

REM 5. Testar export (rápido)
rotinas\export_sheets.bat

REM 6. Testar sync incremental (DEMORADO - 45 min)
REM ATENÇÃO: Só execute se tiver tempo!
rotinas\sync_incremental.bat
```

### Teste de Agendamento

**Depois de configurar, teste executando manualmente:**

```
1. Abrir Agendador de Tarefas
2. Navegar até a tarefa criada
3. Clicar com botão direito → "Executar"
4. Monitorar execução na aba "Histórico"
```

---

## 📊 Monitoramento

### Verificar Logs

**Log consolidado (todas rotinas):**
```
C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\logs\rotinas.log
```

**Exemplo de conteúdo:**
```
[20/08/2026 01:00:00] Iniciando Backup BD
[20/08/2026 01:08:32] Backup BD concluido com sucesso
[20/08/2026 06:00:00] Iniciando Health Check
[20/08/2026 06:00:12] Health Check concluido - Sistema saudavel
[20/08/2026 08:00:00] Iniciando Sync INCREMENTAL
[20/08/2026 08:45:23] Sync INCREMENTAL concluido com sucesso
```

**Logs individuais:**
```
logs\sync_full.log          - Sync completa
logs\sync_incremental.log   - Sync incremental
logs\backup.log             - Backup BD
logs\health_check.log       - Health check
logs\export.log             - Exports Google Sheets
logs\export_analise.log     - Export análise
logs\export_funil.log       - Export funil
logs\export_jade.log        - Export Jade
logs\export_candidaturas.log - Export candidaturas
```

### Verificar Histórico no Agendador

```
1. Abrir Agendador de Tarefas
2. Selecionar a tarefa
3. Aba "Histórico"
4. Verificar:
   - Código de saída 0 = Sucesso
   - Código de saída 1 = Erro
```

### Verificar Última Sincronização (SQL)

```sql
-- Abrir pgAdmin ou psql
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire

-- Query:
SELECT
    sync_type,
    sync_entity,
    status,
    start_time AT TIME ZONE 'America/Sao_Paulo' as inicio,
    end_time AT TIME ZONE 'America/Sao_Paulo' as fim,
    EXTRACT(EPOCH FROM (end_time - start_time))/60 as duracao_min,
    records_processed,
    records_updated
FROM sync_log
WHERE sync_type IN ('FULL', 'INCREMENTAL')
ORDER BY start_time DESC
LIMIT 10;
```

---

## 🚨 Troubleshooting

### Problema 1: Tarefa não executa

**Sintomas:** Tarefa agendada mas não roda

**Soluções:**
1. Verificar se "Executar independentemente do usuário estar conectado" está marcado
2. Verificar se usuário tem permissões de administrador
3. Verificar se senha do usuário está correta
4. Tentar mudar para "Executar somente quando o usuário estiver conectado" (teste)

### Problema 2: Script falha com erro

**Sintomas:** Código de saída 1 no histórico

**Soluções:**
1. Executar script manualmente no CMD
2. Verificar log específico em `logs/`
3. Verificar se Python está no PATH
4. Verificar se .env está configurado
5. Verificar conectividade com PostgreSQL e API Inhire

### Problema 3: Script não encontra arquivo

**Sintomas:** Erro "cannot find file"

**Soluções:**
1. Verificar campo "Iniciar em" está preenchido:
   ```
   C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire
   ```
2. Verificar caminho completo do .bat no campo "Programa/script"
3. Usar caminhos com aspas se tiver espaços

### Problema 4: Sync demora muito (>90 min)

**Sintomas:** Sync incremental leva mais de 1h30

**Diagnóstico:**
```sql
-- Verificar skip rate (deve ser >70%)
SELECT
    sync_entity,
    records_processed,
    records_skipped,
    ROUND((records_skipped::numeric / NULLIF(records_processed, 0) * 100), 2) as skip_rate_pct
FROM sync_log
WHERE sync_type = 'INCREMENTAL'
ORDER BY start_time DESC
LIMIT 20;
```

**Soluções:**
- Skip rate < 50%: Executar Sync FULL
- Skip rate OK mas lento: Verificar índices do BD
- Persistente: Contatar suporte

### Problema 5: Export falha com "grid limits"

**Sintomas:** Export Google Sheets falha

**Soluções:**
1. Script `export_relatorio_candidaturas.py` tem expansão automática
2. Outros scripts: Expandir aba manualmente no Google Sheets
3. Verificar se token OAuth está válido (token.pickle)

---

## 📧 Configurar Notificações por Email (Opcional)

### Windows PowerShell

Criar script `rotinas\notificar_erro.ps1`:

```powershell
param([string]$tarefa, [string]$erro)

$smtp = "smtp.gmail.com"
$port = 587
$username = "seu-email@gmail.com"
$password = "sua-senha-app"
$from = "inhire-sync@localhost"
$to = "seu-email@gmail.com"
$subject = "[ERRO] Rotina Inhire: $tarefa"
$body = "Erro na execução de: $tarefa`n`nDetalhes: $erro"

$credential = New-Object System.Management.Automation.PSCredential($username, (ConvertTo-SecureString $password -AsPlainText -Force))

Send-MailMessage -SmtpServer $smtp -Port $port -UseSsl -Credential $credential -From $from -To $to -Subject $subject -Body $body
```

**Modificar .bat para chamar em caso de erro:**

```batch
python sync_incremental_completo.py --completa --yes >> logs\sync_incremental.log 2>&1

if errorlevel 1 (
    powershell -File rotinas\notificar_erro.ps1 -tarefa "Sync Incremental" -erro "Ver logs\sync_incremental.log"
    exit /b 1
)
```

---

## 📝 Checklist de Configuração

### Antes de Configurar
- [ ] Python instalado e no PATH
- [ ] PostgreSQL 18 instalado
- [ ] Arquivo .env configurado com credenciais
- [ ] Google Sheets OAuth configurado (token.pickle existe)
- [ ] Testado `python health_check.py` com sucesso

### Configuração Essencial (Mínimo)
- [ ] Tarefa 1: Backup Diário (01:00)
- [ ] Tarefa 3: Rotina Diária Manhã (08:00)
- [ ] Tarefa 5: Rotina Semanal Domingo (02:00)

### Configuração Completa (Recomendado)
- [ ] Tarefa 2: Health Check (06:00)
- [ ] Tarefa 4: Sync Incremental Noite (20:00)
- [ ] Tarefa 6: Export Funil Semanal (Segunda 09:00)

### Validação
- [ ] Testado cada script manualmente
- [ ] Executado tarefa manualmente no Agendador
- [ ] Verificado logs após primeira execução
- [ ] Confirmado dados no BD atualizaram
- [ ] Confirmado exports no Google Sheets

---

## 🎯 Resumo de Ações

### Hoje (20-30 minutos)
1. ✅ Abrir Agendador de Tarefas do Windows
2. ✅ Criar pasta "Inhire" (organização)
3. ✅ Criar 6 tarefas essenciais (copiar configurações acima)
4. ✅ Testar execução manual de pelo menos 1 tarefa
5. ✅ Verificar logs em `logs/rotinas.log`

### Amanhã (Validação)
1. ✅ Verificar se Backup executou às 01:00
2. ✅ Verificar se Health Check executou às 06:00
3. ✅ Verificar se Rotina Diária executou às 08:00
4. ✅ Conferir logs de cada rotina
5. ✅ Validar dados atualizados no PostgreSQL

### Próximos 7 Dias (Monitoramento)
1. ✅ Verificar execução diária (Segunda a Sábado)
2. ✅ Verificar Rotina Semanal no Domingo
3. ✅ Ajustar horários se necessário
4. ✅ Revisar logs para identificar problemas
5. ✅ Considerar adicionar mais exports se necessário

---

**Fim do Guia**

**Suporte:** Consultar `ROTINAS_AGENDAMENTO.md` para detalhes técnicos completos

**Última Atualização:** 2026-08-20
