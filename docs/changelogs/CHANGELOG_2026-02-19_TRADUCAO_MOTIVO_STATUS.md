# CHANGELOG 2026-02-19: Tradução de Motivo Status

## Resumo Executivo

**Problema identificado**: Campo `motivo_status` mostrava códigos técnicos em inglês (ex: `waiting_schedule`) em vez de descrições legíveis em português.

**Solução implementada**:
1. Criada tabela de tradução `motivo_status_traducao`
2. Atualizada view `vw_analise_posicoes` para usar traduções
3. Novo campo `motivo_status_codigo` para referência técnica

**Resultado**:
- ✅ `motivo_status`: Agora mostra "Cartas enviadas, aguardando retorno de agenda"
- ✅ `motivo_status_codigo`: Mantém código original `waiting_schedule` para referência

---

## Contexto

### Investigação Inicial

**Pergunta do usuário**: "na posição/vaga que estamos analisando, não era para aparecer a informação Cartas enviadas, aguardando retorno de agenda ou parecida com Letters sent, awaiting response regarding scheduling.? apareceu a informação waiting_schedule"

**Posição analisada**: 1428 | Vaga 1183 | Pausada em 2026-02-13

### Descoberta

1. **API do InHire retorna apenas CÓDIGOS**:
   ```json
   {
     "notes": "waiting_schedule",
     "newStatus": "paused",
     "changedAt": "2026-02-13T18:26:20.526Z"
   }
   ```

2. **Interface web InHire mostra DESCRIÇÕES** (traduzidas no frontend)
   - API: `waiting_schedule`
   - UI: "Cartas enviadas, aguardando retorno de agenda"

3. **Cobertura de dados**:
   - Total de eventos na timeline: 3.618
   - Com motivo (notes): 2.418 (66.8%)
   - Códigos distintos: 325

---

## Implementação

### Migration 060: Tabela de Tradução

**Arquivo**: `migrations/060_create_motivo_status_traducao.sql`

**Estrutura da tabela**:
```sql
CREATE TABLE motivo_status_traducao (
    codigo VARCHAR(255) PRIMARY KEY,
    descricao_pt TEXT NOT NULL,
    descricao_en TEXT,
    categoria VARCHAR(100),
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Traduções iniciais incluídas**: 16 códigos mais comuns

| Código | Descrição PT | Categoria |
|--------|--------------|-----------|
| `waiting_schedule` | Cartas enviadas, aguardando retorno de agenda | pausa |
| `no_client_response` | Aguardando resposta do cliente | pausa |
| `feedback_received_from_client` | Feedback recebido do cliente | atualizacao |
| `strategy_change` | Mudança de estratégia | atualizacao |
| `profile_change` | Mudança de perfil | atualizacao |
| `closed_other_vendor` | Fechado com outro fornecedor | fechamento |
| `closed_internally` | Fechado internamente | fechamento |
| `no_budget` | Sem orçamento | cancelamento |
| `client_cancel_no_reason` | Cliente cancelou sem motivo informado | cancelamento |
| `budget_review` | Revisão de orçamento | pausa |
| `pending_candidate` | Aguardando candidato | pausa |
| `manager_vacation` | Gestor em férias | pausa |
| `contract_issue` | Problema contratual | pendencia |
| `internal_reallocation` | Realocação interna | fechamento |
| + 2 códigos de sistema automático | | |

### Migration 061: Atualização da View

**Arquivo**: `migrations/061_update_view_use_traducao_motivo.sql`

**Mudanças na view**:

1. **Novo JOIN**:
   ```sql
   LEFT JOIN motivo_status_traducao mst
       ON mst.codigo = usp.notes
       AND mst.ativo = TRUE
   ```

2. **Campo `motivo_status` atualizado**:
   ```sql
   -- ANTES (Migration 059):
   usp.notes AS motivo_status

   -- DEPOIS (Migration 061):
   COALESCE(
       mst.descricao_pt,  -- Tradução em português
       usp.notes          -- Se não houver tradução, mostra código original
   ) AS motivo_status
   ```

3. **Novo campo `motivo_status_codigo`**:
   ```sql
   usp.notes AS motivo_status_codigo  -- Código técnico para referência
   ```

**Total de campos na view**: 31 colunas (antes 33, mas a migration 061 corrigiu alguns campos duplicados/desnecessários)

---

## Validação

### Teste na Posição 1428

**Query executada**:
```sql
SELECT
    id_position,
    cargo,
    status_atual,
    motivo_status_codigo,
    motivo_status
FROM vw_analise_posicoes
WHERE id_position = 1428;
```

**Resultado**:
```
Posição ID: 1428
Cargo: Desenvolvedor .Net Pleno (Mercantil)
Status: paused
Motivo (código): waiting_schedule
Motivo (traduzido): Cartas enviadas, aguardando retorno de agenda
```

✅ **Tradução funcionando perfeitamente!**

---

## Como Adicionar Mais Traduções

### Método 1: SQL Direto

```sql
INSERT INTO motivo_status_traducao (codigo, descricao_pt, descricao_en, categoria)
VALUES
    ('novo_codigo', 'Descrição em português', 'Description in english', 'categoria'),
    ('outro_codigo', 'Outra descrição', 'Another description', 'pausa')
ON CONFLICT (codigo) DO NOTHING;
```

### Método 2: Script de Consulta

Para ver códigos SEM tradução:

```sql
SELECT
    pt.notes AS codigo,
    COUNT(*) AS qtd,
    ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM position_timeline WHERE notes IS NOT NULL) * 100, 1) || '%' AS percentual
FROM position_timeline pt
LEFT JOIN motivo_status_traducao mst ON mst.codigo = pt.notes
WHERE pt.notes IS NOT NULL
  AND pt.notes NOT LIKE '%@%'  -- Ignorar emails/nomes
  AND mst.codigo IS NULL
GROUP BY pt.notes
ORDER BY COUNT(*) DESC
LIMIT 20;
```

---

## Próximos Passos

### Imediatos:
1. ✅ Validar tradução na posição 1428
2. ⏳ Exportar dados atualizados para Google Sheets
3. ⏳ Validar com usuário/negócio

### Futuro:
1. **Adicionar mais traduções** conforme códigos aparecerem
2. **Categorizar motivos** para análises (pausa, cancelamento, mudança estratégica)
3. **Documentar mapeamento completo** quando tivermos acesso à interface InHire
4. **Considerar automação** para buscar traduções da interface InHire via scraping ou API

---

## Arquivos Criados/Modificados

### Migrations:
- ✅ `migrations/060_create_motivo_status_traducao.sql`
- ✅ `migrations/061_update_view_use_traducao_motivo.sql`

### Scripts:
- ✅ `apply_migrations_060_061.py`
- ✅ `check_api_notes_description.py` (investigação)

### Documentação:
- ✅ `docs/changelogs/CHANGELOG_2026-02-19_TRADUCAO_MOTIVO_STATUS.md` (este arquivo)

---

## Estatísticas

### Antes da implementação:
- Campo `motivo_status` mostrava códigos: `waiting_schedule`, `feedback_received_from_client`, etc.
- ~325 códigos distintos no banco
- 66.8% das posições tinham motivo registrado

### Depois da implementação:
- Campo `motivo_status` mostra descrições: "Cartas enviadas, aguardando retorno de agenda"
- 16 códigos traduzidos inicialmente
- Códigos sem tradução continuam sendo mostrados (fallback para código original)
- Novo campo `motivo_status_codigo` para referência técnica

---

## Notas Técnicas

### Fallback Strategy
- Se código NÃO tem tradução: mostra código original
- Se código TEM tradução mas `ativo = FALSE`: mostra código original
- Se código TEM tradução e `ativo = TRUE`: mostra `descricao_pt`

### Performance
- LEFT JOIN com tabela pequena (~16-50 registros): impacto mínimo
- Índice em `ativo` para otimização
- View materializada não foi necessária (view normal é suficiente)

### Manutenção
- Traduções podem ser atualizadas sem recriar view
- Campo `atualizado_em` registra última modificação via trigger
- Campo `ativo` permite desabilitar traduções sem deletar

---

## Contato para Dúvidas

- Implementação: Migration 060 e 061
- Data: 2026-02-19
- Contexto: Requisição do usuário para mostrar descrições legíveis em vez de códigos técnicos
