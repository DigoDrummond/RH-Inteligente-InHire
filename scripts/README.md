# Scripts Auxiliares

Esta pasta contém scripts auxiliares organizados por categoria.

## Estrutura

### `/analise`
Scripts para análise de dados e métricas:
- `analise_contratacoes_pretensao.py` - Análise de contratações e pretensões salariais
- `analise_funil_performance.py` - Análise de performance do funil
- `analise_funil_simples.py` - Análise simplificada do funil

### `/debug`
Scripts para debug e verificação:
- `check_status.py` - Verificação de status geral
- `check_vagas_status.py` - Verificação de status de vagas
- `comparar_posicoes_abertas.py` - Comparação de posições abertas
- `debug_posicoes.py` - Debug de posições
- `verificar_contratacoes_salario.py` - Verificação de contratações e salários
- `verificar_custom_fields.py` - Verificação de custom fields
- `verificar_indicacoes.py` - Verificação de indicações
- `listar_custom_fields_disponiveis.py` - Lista custom fields disponíveis
- `testar_api_custom_fields.py` - Testa API de custom fields
- `sync_custom_fields_only.py` - Sincroniza apenas custom fields

### `/export`
Scripts para exportação de dados:
- `export_posicoes_atualizado.py` - Exporta posições atualizadas
- `export_to_sheets.py` - Exporta dados para Google Sheets
- `extrair_contratacoes_pretensao_final.py` - Extrai dados finais de contratações
- `update_exports.py` - Atualiza todos os exports

## Uso

Todos os scripts devem ser executados a partir da raiz do projeto:

```bash
python scripts/analise/analise_funil_simples.py
python scripts/debug/debug_posicoes.py
python scripts/export/update_exports.py
```

## Nota

Estes scripts são auxiliares e não fazem parte do fluxo principal de sincronização.
Para sincronização, use `run_sync.py` na raiz do projeto.
