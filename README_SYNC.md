# Sincronização InHire - Guia de Uso

Este documento explica como executar as sincronizações de dados da API InHire para o banco de dados PostgreSQL.

## Arquivos de Sincronização

### 1. `run_sync_full.py` - Sincronização Completa

**Quando usar:**
- Primeira sincronização do sistema
- Após mudanças significativas na estrutura de dados
- Quando precisar reprocessar todos os dados

**Características:**
- Importa **TODOS** os dados da API sem filtros
- Tempo estimado: **~55 minutos**
- Volume estimado: **~104.558 registros**
- Não compara datas, apenas insere/atualiza tudo

**Como executar:**
```bash
python run_sync_full.py
```

---

### 2. `run_sync_incremental.py` - Sincronização Incremental

**Quando usar:**
- Atualizações diárias/rotineiras
- Capturar mudanças recentes
- Sincronização rápida e eficiente

**Características:**
- Compara `updated_at_inhire` (BD) com `updatedAt` (API)
- Atualiza **apenas registros modificados**
- Tempo estimado: **~2-5 minutos**
- **IMPORTANTE:** Captura mudanças de status automaticamente (ex: OPEN → CLOSED)

**Estratégia de Sincronização Incremental:**
1. Busca TODOS os registros da API (sem filtro de status)
2. Para cada registro:
   - Se NÃO existe no BD: **CRIA**
   - Se existe no BD:
     - Compara `updated_at_inhire` (BD) com `updatedAt` (API)
     - Se API é mais recente: **ATUALIZA**
     - Se BD é mais recente ou igual: **PULA**

**Como executar:**
```bash
python run_sync_incremental.py
```

---

## Entidades Sincronizadas

Ambos os scripts sincronizam as seguintes entidades (nesta ordem):

1. **Vagas** (Jobs)
2. **Posições** (Positions)
3. **Candidaturas** (Job Talents)
4. **Talentos** (Talents)
5. **Requisições** (Requisitions)
6. **Scorecard Interviews**
7. **Scorecard Jobs**
8. **Vaga Tags**
9. **Clientes**
10. **Custom Fields**

---

## Exemplos de Uso

### Primeira vez no sistema:
```bash
# Executar sincronização completa
python run_sync_full.py
```

### Atualização diária:
```bash
# Executar sincronização incremental
python run_sync_incremental.py
```

### Via Claude Code:
Você pode solicitar a execução diretamente:
- "Execute a sincronização incremental"
- "Rode o run_sync_incremental.py"
- "Sincronize os dados da InHire"

---

## Diferenças entre Full e Incremental

| Característica | Full | Incremental |
|---------------|------|-------------|
| **Tempo** | ~55 min | ~2-5 min |
| **Estratégia** | Importa tudo | Compara datas |
| **Volume** | ~104.558 registros | Apenas mudanças |
| **Filtros** | Nenhum | Comparação de `updated_at` |
| **Mudanças de status** | ✓ Captura | ✓ Captura |
| **Uso recomendado** | Primeira vez / Reset | Rotina diária |

---

## Importante: Captura de Mudanças de Status

**Ambos os scripts capturam mudanças de status corretamente!**

Exemplos de mudanças capturadas:
- Vaga: `OPEN` → `CLOSED`
- Posição: `open` → `closed`
- Candidatura: `ACTIVE` → `REJECTED` / `HIRED`

**Princípio aplicado:**
- ✓ Sempre compara datas primeiro
- ✗ Nunca filtra por status antes da comparação

Isso garante que se uma vaga foi fechada na API, a sincronização incremental detecta a mudança de data e atualiza o status no BD.

---

## Estrutura do Código

### Arquivo Principal (Legado)
- `run_sync.py` - Aceita parâmetros `--full` ou `--incremental`

### Novos Arquivos (Recomendado)
- `run_sync_full.py` - Execução direta da sincronização completa
- `run_sync_incremental.py` - Execução direta da sincronização incremental

### Serviço de Sincronização
- `services/sync_service.py` - Contém toda a lógica de sincronização
  - Métodos `_sync_*_full()` - Sincronização completa por entidade
  - Métodos `_sync_*_incremental()` - Sincronização incremental por entidade

---

## Troubleshooting

### Sincronização incremental não está capturando mudanças de status
- ✓ **Correto:** O código atual compara datas para TODAS as entidades
- ✗ **Antigo (bug corrigido):** Filtrava por status antes de comparar datas

### Tempo de execução muito longo
- Use `run_sync_incremental.py` em vez de `run_sync_full.py`
- Sincronização incremental é 10-20x mais rápida

### Erros de encoding
- O código já inclui fix automático de encoding UTF-8
- Variáveis de ambiente são configuradas automaticamente

---

## Logs e Monitoramento

Durante a execução, você verá:
- Progresso em tempo real (ex: "Vagas processadas: 50")
- Estatísticas ao final:
  - Registros processados
  - Novos criados
  - Atualizados
  - Ignorados (sem mudanças)
  - Falhas

---

## Contato e Suporte

Para dúvidas ou problemas, consulte a documentação do projeto ou entre em contato com a equipe de desenvolvimento.
