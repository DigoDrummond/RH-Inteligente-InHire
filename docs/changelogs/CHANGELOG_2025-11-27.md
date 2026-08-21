# CHANGELOG - 2025-11-27

## Implementação das Recomendações 1 e 5

### ✅ RECOMENDAÇÃO 5: Corrigir link talento_id nas candidaturas

**Status:** CONCLUÍDA

**Problema Identificado:**
- A tabela `candidaturas` tinha `talent_inhire_id` (String) preenchido, mas o campo `talento_id` (FK para `talentos`) estava vazio
- Isso impedia queries relacionais entre candidaturas e talentos
- **Root Cause:** `services/database_service.py:upsert_candidatura()` não fazia lookup do talento local

**Solução Implementada:**

1. **Modificação do Código Sync** (`services/database_service.py:234-267`):
```python
# Lookup do talento no banco local para vincular FK
talento = self.session.query(Talento).filter_by(inhire_id=cand_api.talentId).first()
talento_id = talento.id if talento else None

# Aplicar em UPDATE e CREATE
existing.talento_id = talento_id  # UPDATE
nova_cand = Candidatura(..., talento_id=talento_id)  # CREATE
```

2. **Script de Correção** (`fix_candidatura_talento_id.py`):
   - Processa registros existentes em lotes de 1,000
   - Faz lookup de talento por `inhire_id`
   - Atualiza `talento_id` FK

**Resultado:**
- ✅ **74,462 candidaturas** vinculadas com sucesso (98.2%)
- ⚠️ **330 candidaturas** órfãs (0.4%) - talentos não existem no banco local
- **53,136 talentos únicos** agora linkados ao funil

**Arquivos Criados/Modificados:**
- `services/database_service.py` (linhas 234-267)
- `fix_candidatura_talento_id.py`

---

### ✅ RECOMENDAÇÃO 1: Padronizar nomes das etapas do funil

**Status:** CONCLUÍDA

**Problema Identificado:**
- **32 nomes únicos** de etapas com variações de capitalização e nomenclatura
- Exemplos:
  - "Bate papo" vs "Bate Papo"
  - "Aguardando Devolutiva AI" vs "Aguardando Devolutiva IA"
  - "Etapa técnica | Talent IA" vs "Etapa Técnica"
  - "Aprovação" vs "Formalização de Proposta"

**Solução Implementada:**

1. **Análise de Variações** (`identificar_variacoes_stage.py`):
   - Identificou 32 variações across 11 ordens
   - Análise case-insensitive
   - Análise de nomes compostos (com "|")

2. **Mapeamento de Padronização**:
```python
STAGE_NAME_MAPPING = {
    "Bate papo | Pessoas e Cultura": "Bate Papo | Pessoas e Cultura",
    "Etapa técnica | Talent IA": "Etapa Técnica",
    "Aguardando Devolutiva AI": "Aguardando Devolutiva IA",
    "Teste Técnico": "Etapa Técnica",
    "Aprovação": "Formalização de Proposta",
    # ... total de 21 mapeamentos
}
```

3. **Script de Padronização** (`padronizar_stage_names_fixed.py`):
   - Usa UPDATE SQL único com CASE/WHEN
   - Evita loops infinitos (problema no script original)
   - Execução atômica

**Resultado:**
- ✅ Redução de **32 → 14 nomes únicos** de etapas
- ✅ **5,317 registros** padronizados
- ✅ Nomenclatura consistente para análises

**Arquivos Criados:**
- `identificar_variacoes_stage.py` - Análise
- `padronizar_stage_names.py` - Script original (tinha bug)
- `padronizar_stage_names_fixed.py` - Versão corrigida

---

## Verificação Completa do Funil

**Script:** `verificar_funil_completo.py`

**Análises Realizadas:**

### Parte 1: Integridade dos Dados
- Total: 75,792 candidaturas
- Status: 53.73% ACTIVE, 41.88% REJECTED, 4.39% DECLINED
- 99.6% com talento_id vinculado
- 53,136 talentos únicos
- 999 vagas com candidaturas

### Parte 2: Distribuição por Etapas
```
Ordem 3 | Inscrição                    | 51,697 (68.21%)
Ordem 1 | Hunting                      | 12,480 (16.47%)
Ordem 4 | Bate Papo | Pessoas e Cultura|  4,759 (6.28%)
Ordem 5 | Etapa Técnica                |  2,448 (3.23%)
Ordem 2 | Abordagem                    |  2,150 (2.84%)
```

### Parte 3: Funil de Conversão (ACTIVE)
- Ordem 1: 5,805 (100.00%)
- Ordem 2: 913 (15.73%)
- Ordem 3: 31,587 (544.13% - entrada direta!)
- Ordem 4: 749 (12.85%)

### Parte 4: Verificação de Consistência

**❌ PROBLEMA 1: Candidaturas Órfãs**
- **330 candidaturas** sem talento_id (0.4%)
- 27 vagas afetadas
- Top vaga: "Engenheiro de dados Especialista - 27/10" (37 órfãs)

**⚠️ PROBLEMA 2: Etapas com Múltiplas Ordens**
- **8 etapas** aparecem em múltiplas ordens:
  - Formalização de Proposta → {6,7,8,9,10,11}
  - Contratação → {7,8,9,10,11}
  - Bate Papo Cliente → {6,7,8,9}
  - Bate Papo | Pessoas e Cultura → {4,5,7}
  - Etapa Técnica → {5,6,8}

**Causa:** A API do InHire permite configurar a mesma etapa em diferentes posições do funil para vagas diferentes. Isso é intencional mas dificulta análises de conversão lineares.

### Parte 5: Métricas de Saúde
- Média de candidaturas/talento: **1.42**
- Talento mais ativo: **32 candidaturas** (Daniela de Lima Neves Murta)

---

## Status dos Background Processes

### ✅ COMPLETADOS:

**1. sync_posicoes_only.py**
- Processados: 545
- Novos: 1
- Atualizados: 3
- Ignorados: 541
- Tempo: 10.9 minutos

**2. sync_requisicoes_only.py**
- Processados: 0
- Nenhuma requisição encontrada na API
- Tempo: 2.7 segundos

**3. fix_candidatura_talento_id.py**
- ✅ 74,462 corrigidos
- ⚠️ 330 não encontrados

**4. padronizar_stage_names_fixed.py**
- ✅ 5,317 registros padronizados
- ✅ 14 nomes únicos finais

### ❌ FALHANDO:

**sync_talentos_incremental.py**
- Erro: `url NOT NULL constraint` em `talento_arquivos`
- Problema já foi corrigido com `fix_talento_arquivos_url.py` anteriormente
- Pode ser re-executado após aplicar migration novamente

---

## Próximos Passos Recomendados

### Opção 1: Investigar Órfãs (330 candidaturas)
- Sincronizar os talentos faltantes da API
- Ou aceitar 0.4% de perda (talentos provavelmente deletados)

### Opção 2: Normalizar Ordens das Etapas
- Definir ordem canônica para cada etapa
- Atualizar candidaturas com ordens inconsistentes
- Criar views/queries que abstraiam a complexidade

### Opção 3: Análises Específicas
- Análise de conversão por vaga (não global)
- Tempo médio em cada etapa
- Identificar gargalos por área/cliente

### Opção 4: Continuar Correções
- Re-aplicar migration para `talento_arquivos.url` como nullable
- Re-executar sync incremental de talentos
- Investigar posições órfãs (0 posições encontradas para vagas específicas)

---

## Scripts Criados

### Correção de Dados
- **fix_candidatura_talento_id.py** - Vincula talento_id em candidaturas
- **padronizar_stage_names_fixed.py** - Padroniza nomes de etapas (versão corrigida)

### Análise
- **identificar_variacoes_stage.py** - Analisa variações de nomes
- **verificar_funil_completo.py** - Verificação completa de integridade e saúde
- **analise_funil_kanban.py** - Análise anterior do funil (pré-correções)

### Observações
- Scripts `padronizar_stage_names.py` e `fix_candidatura_talento_id.py` (versões originais) têm bug de loop infinito - NÃO usar
- Usar sempre as versões `_fixed` quando disponíveis

---

## Impacto das Mudanças

### Positivo
✅ Queries relacionais entre candidaturas-talentos agora funcionam
✅ Nomenclatura consistente para análises
✅ Redução de 32 → 14 etapas únicas
✅ 99.6% de integridade de dados
✅ Funil verificado e documentado

### Pendente
⚠️ 330 candidaturas órfãs (0.4%)
⚠️ 8 etapas com ordens múltiplas (comportamento da API)
⚠️ Sync de talentos falhando (url constraint)

---

**Data:** 2025-11-27
**Responsável:** Claude Code + Marcos Santiago
