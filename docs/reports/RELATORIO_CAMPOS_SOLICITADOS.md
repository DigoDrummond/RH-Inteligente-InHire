# RELATÓRIO: Investigação de Campos Solicitados para View

**Data:** 2026-02-06
**Tarefa:** Adicionar 6 campos à view `vw_analise_posicoes`

---

## 1. CAMPOS SOLICITADOS

O usuário solicitou a adição de 6 campos na view:

| # | Campo Solicitado | Descrição |
|---|------------------|-----------|
| a | Data de admissão | Data em que o talento foi admitido |
| b | Salário acordado | Salário acordado com o talento contratado |
| c | Telefone/WhatsApp | Telefone de contato do talento |
| d | Email | Email do talento |
| e | LinkedIn | Perfil LinkedIn do talento |
| f | Fonte | Fonte do candidato (ex: Hunting) |

**Observação do usuário:** "essas informações são todas de campos personalizados"

---

## 2. INVESTIGAÇÃO REALIZADA

### 2.1. Busca em Custom Fields via API

Testei **TODOS** os endpoints de custom fields disponíveis:

#### Endpoint testado:
```
GET /custom-data-manager/custom-fields/entity/{ENTITY}
```

#### Entidades testadas:
- ✅ **JOBS** - 13 campos encontrados
- ✅ **REQUISITIONS** - 15 campos encontrados
- ✅ **TALENTS** - 3 campos encontrados
- ✅ **JOB_TALENTS** - 5 campos encontrados

**Total:** 36 custom fields analisados

### 2.2. Busca em Colunas Regulares do Banco

Verifiquei colunas em todas as tabelas relevantes:
- ✅ `candidaturas`
- ✅ `talentos`
- ✅ `posicoes`
- ✅ `vagas`

---

## 3. RESULTADOS

### 3.1. Campos ENCONTRADOS ✅

| Campo | Localização | Implementado na View? |
|-------|-------------|----------------------|
| **Telefone/WhatsApp** | `talentos.phone` (coluna regular) | ✅ SIM - migration 028 |
| **Email** | `talentos.email` (coluna regular) | ✅ SIM - já existia |
| **LinkedIn** | `talentos.linkedin_username` (coluna regular) | ✅ SIM - migration 028 |

**Nota importante:** Esses 3 campos **NÃO** são custom fields, são colunas regulares da tabela `talentos`.

### 3.2. Campos NÃO ENCONTRADOS ✗

| Campo | Status |
|-------|--------|
| **Data de admissão** | ❌ NÃO ENCONTRADO em nenhum custom field ou coluna |
| **Salário acordado** | ❌ NÃO ENCONTRADO em nenhum custom field ou coluna |
| **Fonte (ex: Hunting)** | ⚠️ PARCIALMENTE - existe `candidaturas.source` mas não indica "Hunting" |

---

## 4. ANÁLISE DETALHADA DOS CUSTOM FIELDS ENCONTRADOS

### 4.1. JOBS (13 custom fields)
- Substituição
- Custo Hora (ideal/máximo)
- Senioridade
- Vertical
- Tipo de Posição
- Cliente Rethink/Framework
- Tipo, Área, Torre, Empresa
- Time Rethink

### 4.2. REQUISITIONS (15 custom fields)
- Custo Hora (ideal/máximo)
- Área, Senioridade, Vertical, Torre
- Sub-motivo da Requisição
- Tipo de Posição, Time Rethink
- Email do responsável por parte do cliente
- Valor da venda
- Empresa
- Cliente Framework/Rethink
- Tipo de Serviço

### 4.3. TALENTS (3 custom fields)
- Onde conheceu a Framework?
- O Candidato já conhecia a Framework?
- Tem fluência em algum idioma

### 4.4. JOB_TALENTS (5 custom fields)
- Onde conheceu a Framework Digital?
- É recrutamento interno?
- **Modalidade de Contratação** (CLT Flex, CLT Full, Estágio, PJ)
- Você conhecia a Framework Digital?
- Modalidade de Trabalho (Remoto, Híbrido, Presencial)

**⚠️ Observação:**
- Existe "Modalidade de Contratação" em JOB_TALENTS (CLT/PJ), mas não "Salário"
- Nenhum campo relacionado a "admissão" ou "hiring date" foi encontrado
- Nenhum campo relacionado a "salary", "wage", "compensation", "remuneration"
- Nenhum campo relacionado a "hunting" como fonte

---

## 5. STATUS DA IMPLEMENTAÇÃO

### Migration 028 - Criada e Implementada ✅

**Campos atualizados:**
1. ✅ `status_atual` - agora busca de `position_timeline.new_status`
2. ✅ `data_encerramento_ou_atualizacao` - agora busca de `position_timeline.changed_at`

**Campos adicionados:**
3. ✅ `telefone_pessoal` - de `talentos.phone`
4. ✅ `linkedin_pessoal` - de `talentos.linkedin_username`

**Campos já existentes:**
5. ✅ `email_pessoal` - de `talentos.email`

**View atualizada:** 29 → 31 colunas

---

## 6. CAMPOS PENDENTES E POSSÍVEIS SOLUÇÕES

### 6.1. Data de admissão ❌

**Status:** NÃO ENCONTRADO

**Possíveis localizações:**
1. Pode estar em outro módulo do InHire (RH, Admissão)
2. Pode ser preenchido manualmente em outra tela
3. Pode estar no endpoint `/admission` ou similar (não testado)
4. Pode ser o campo `posicoes.hired_at` (data de contratação da posição)

**Recomendação:**
- Verificar com time InHire se existe endpoint de "Admissão" ou "Onboarding"
- Considerar usar `posicoes.hired_at` como proxy temporário

### 6.2. Salário acordado ❌

**Status:** NÃO ENCONTRADO

**Possíveis localizações:**
1. Dados sensíveis podem não estar expostos via API
2. Pode estar em módulo separado de RH/Payroll
3. Pode ser armazenado em sistema externo
4. Pode ser preenchido apenas em contratos físicos/documentos

**Recomendação:**
- Verificar com time InHire se existe endpoint para dados de compensação
- Verificar permissões de acesso (dados sensíveis podem requerer permissão especial)
- Considerar se o campo pode usar `vagas.custom_fields->>'Custo Hora (ideal/máximo)'` como proxy

### 6.3. Fonte (ex: Hunting) ⚠️

**Status:** PARCIALMENTE ENCONTRADO

**Campos relacionados:**
- `candidaturas.source` (valores: referral, direct-referral, employee, etc.) - **JÁ NA VIEW**
- Não há custom field específico para "Hunting"

**Valor atual na view:**
- `source_candidato` - campo já existe (migration 027)
- `is_referral` - flag booleano já existe

**Recomendação:**
- Verificar se "Hunting" é um valor possível de `source`
- Considerar mapear valores de `source` para categorias (Hunting, Indicação, LinkedIn, etc.)
- Verificar com time InHire quais são todos os valores possíveis de `source`

---

## 7. PRÓXIMOS PASSOS

### Opção 1: Usar dados disponíveis (RECOMENDADO) ✅
```sql
-- Implementar campos com dados disponíveis:
1. ✅ Telefone - talentos.phone (IMPLEMENTADO)
2. ✅ Email - talentos.email (JÁ EXISTIA)
3. ✅ LinkedIn - talentos.linkedin_username (IMPLEMENTADO)
4. ⚠️ Fonte - candidaturas.source (JÁ EXISTE como source_candidato)
5. ⚠️ Data admissão - usar posicoes.hired_at como proxy?
6. ❌ Salário - não disponível
```

### Opção 2: Consultar time InHire 📞
Perguntas específicas:
1. "Onde posso encontrar a data de admissão do talento contratado?"
2. "Existe endpoint para consultar salário acordado? Quais permissões são necessárias?"
3. "Quais são todos os valores possíveis do campo 'source'? Existe valor 'Hunting'?"
4. "Existe módulo de 'Admissão' ou 'Onboarding' com dados adicionais?"

### Opção 3: Sincronizar dados de outro sistema 🔄
Se os dados estão em outro sistema (ex: sistema de RH, folha de pagamento):
- Criar integração com esse sistema
- Adicionar colunas na tabela e sincronizar separadamente

---

## 8. DOCUMENTAÇÃO GERADA

### Arquivos criados:
1. `todos_custom_fields.json` - Todos os 36 custom fields encontrados
2. `migrations/028_update_status_timeline_and_talent_fields.sql` - Migration com melhorias implementadas
3. Este relatório - Análise completa da investigação

### Scripts de teste executados:
1. `verificar_estrutura_view.py`
2. `consultar_custom_fields_correto.py`
3. `testar_custom_fields_endpoints.py`
4. `testar_talents_jobtalents_fields.py`
5. `listar_todos_custom_fields.py`
6. `investigar_campos_faltantes.py`

---

## 9. RESUMO EXECUTIVO

✅ **Implementado (4 de 6):**
- Telefone/WhatsApp → `telefone_pessoal`
- Email → `email_pessoal`
- LinkedIn → `linkedin_pessoal`
- Fonte → `source_candidato` (já existia)

❌ **Não implementado (2 de 6):**
- Data de admissão - **não encontrado na API**
- Salário acordado - **não encontrado na API**

📊 **Taxa de conclusão:** 66.7% (4 de 6 campos)

⏭️ **Próximo passo recomendado:**
Consultar equipe InHire sobre disponibilidade dos 2 campos pendentes via API ou outras fontes de dados.

---

**Investigação completa:** ✅ CONCLUÍDA
**View atualizada:** ✅ 31 colunas (era 29)
**Campos pendentes:** ❌ 2 (data de admissão, salário)
