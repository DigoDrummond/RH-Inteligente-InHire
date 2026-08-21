# CHANGELOG - 2026-02-06 - Adição do Campo Gestor

## Problema Reportado

O campo `user_name` (gestor) não estava sendo preenchido, mesmo havendo essa informação na API do InHire.

**Exemplo citado:** Vaga ID 1178
- No InHire aparece: **Gestor(a): Bruno Pereira** (ou Lidiane Pereira conforme dados atuais)
- Na view: Campo não existia ❌

## Diagnóstico

### Investigação Realizada

1. **Verificação da vaga 1178:**
   - `responsavel` = Cristian de Freitas Benigno (da requisição) ✅
   - `recrutador_vaga` = Jade Caroline Souza de Oliveira (da vaga) ✅
   - `gestor` = NÃO EXIBIDO ❌

2. **Descoberta nos custom_fields:**
   ```json
   {
     "Gestor": "Lidiane Pereira"
   }
   ```
   O campo "Gestor" existe nos custom_fields mas não estava sendo extraído!

3. **Campo `manager_id` na tabela vagas:**
   - Existe na estrutura: ✅
   - Preenchido em: **64.7%** das vagas (755 de 1167)
   - Mas não está sendo usado atualmente

4. **Campo "Gestor" nos custom_fields:**
   - Existe em: **12.7%** das vagas (148 de 1167)
   - **NÃO estava na view** ❌

### Conclusão

A view tinha apenas 2 campos de responsáveis:
- `responsavel` - user_name da **requisição**
- `recrutador_vaga` - user_name da **vaga**

Mas faltava:
- `gestor` - custom_fields->>'Gestor' da **vaga**

## Solução Implementada

### Alteração na View

Adicionado novo campo após `recrutador_vaga`:

```sql
-- ANTES: 29 colunas
...
r.user_name AS responsavel,
v.user_name AS recrutador_vaga,
pp.datas_inicio_pausa AS inicio_pendencia_cliente,
...

-- DEPOIS: 30 colunas
...
r.user_name AS responsavel,
v.user_name AS recrutador_vaga,
v.custom_fields->>'Gestor' AS gestor,  -- ⭐ NOVO
pp.datas_inicio_pausa AS inicio_pendencia_cliente,
...
```

### Hierarquia de Responsáveis

Agora a view tem **3 campos** de pessoas responsáveis:

1. **`responsavel`** (da requisição)
   - Origem: `requisicoes.user_name`
   - Preenchimento: 58.2% das posições (484 de 831)
   - Exemplo: "Cristian de Freitas Benigno"

2. **`recrutador_vaga`** (da vaga)
   - Origem: `vagas.user_name`
   - Preenchimento: 100% das posições
   - Exemplo: "Jade Caroline Souza de Oliveira"

3. **`gestor`** (custom field da vaga) ⭐ **NOVO**
   - Origem: `vagas.custom_fields->>'Gestor'`
   - Preenchimento: 13.4% das posições (111 de 831)
   - Exemplo: "Lidiane Pereira"

## Resultados

### Após Implementação

- ✅ View agora tem **30 colunas** (antes: 29)
- ✅ **111 posições** (13.4%) com campo gestor preenchido
- ✅ **720 posições** (86.6%) sem gestor (NULL - normal quando não informado)

### Posição 1178 (Exemplo Reportado)

**ANTES:**
```
Cargo: Desenvolvedor OutSystems Junior
Responsável: Cristian de Freitas Benigno
Recrutador: Jade Caroline Souza de Oliveira
Gestor: [CAMPO NÃO EXISTIA] ❌
```

**DEPOIS:**
```
Cargo: Desenvolvedor OutSystems Junior
Responsável: Cristian de Freitas Benigno
Recrutador: Jade Caroline Souza de Oliveira
Gestor: Lidiane Pereira ✅
Cliente: Unimed BH
```

### Exemplos de Posições com Gestor

| ID | Cargo | Responsável | Recrutador | Gestor |
|----|-------|-------------|------------|--------|
| 1543 | Estagiário(a) de Social Media | Janine Christie | Bruna Madureira | Rafael Bretas |
| 1533 | Desenvolvedor Python Sênior | Théo Bicalho | Clara Diniz | Théo Bicalho |
| 1530 | Desenvolvedor Node Sênior | Iggor Castor | Jade Caroline | Marcelo Borba |
| 1528 | Desenvolvedor Fullstack Python Senior | Rafael Gontijo | Jade Caroline | Ûrley Duque |
| 1527 | Analista de Eventos Pleno | Janine Christie | Thainara de Souza | Rafael Bretas |

## Arquivos Modificados

### 1. View `vw_analise_posicoes`
- **Arquivo:** `migrations/025_add_gestor_field_to_view.sql`
- **Alteração:** Adicionado campo `gestor` entre `recrutador_vaga` e `inicio_pendencia_cliente`

### 2. Script de Exportação
- **Arquivo:** `export_posicoes_oauth.py`
- **Alteração:** Adicionado campo `gestor` no SELECT

### 3. Scripts de Investigação
- `investigar_user_name_vaga_1178.py` - Diagnóstico inicial
- `investigar_campo_gestor.py` - Descoberta do campo nos custom_fields
- `verificar_manager_id.py` - Análise do campo manager_id e estatísticas
- `adicionar_campo_gestor.py` - Implementação e validação

### 4. Documentação
- `docs/changelogs/CHANGELOG_2026-02-06_ADICAO_CAMPO_GESTOR.md` - Este changelog

## Exportação para Google Sheets

✅ **Dados exportados com sucesso**

- URL: https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw/
- Aba: Teste_API
- Colunas: **30** (antes: 29)
- Registros: 831 posições + header
- Células: **24.960** atualizadas (antes: 24.128)
- Data: 2026-02-06

## Impacto

### Benefícios

1. ✅ Informação de gestor agora visível quando disponível
2. ✅ Hierarquia completa: Responsável → Recrutador → Gestor
3. ✅ 111 posições agora mostram o gestor
4. ✅ Alinhamento com dados exibidos no InHire
5. ✅ Melhor rastreabilidade de responsabilidades

### Sem Impacto Negativo

- Não altera cálculos existentes
- Não quebra integrações (apenas adiciona coluna)
- Campo NULL quando gestor não informado (comportamento esperado)

## Observações

### Sobre o Preenchimento

**13.4% de preenchimento** é esperado porque:
- Nem todas as vagas têm um gestor específico designado
- Campo é opcional no InHire
- Vagas mais recentes/estruturadas tendem a ter esse campo
- Algumas vagas são gerenciadas diretamente pelo responsável/recrutador

### Diferença entre Responsável, Recrutador e Gestor

- **Responsável:** Pessoa que requisitou a vaga (da requisição)
- **Recrutador:** Pessoa responsável pelo processo seletivo (da vaga)
- **Gestor:** Gestor/gerente do cliente que irá receber o contratado

### Campo `manager_id`

Existe um campo `manager_id` na tabela vagas que está preenchido em 64.7% dos casos, mas:
- Atualmente armazena apenas o ID
- Não temos tabela de "managers" para fazer JOIN
- O campo "Gestor" nos custom_fields já traz o nome (mais útil)
- Futuro: podemos usar `manager_id` para enriquecer dados se necessário

## Validação

### Testes Realizados

1. ✅ Posição 1178 - gestor preenchido corretamente
2. ✅ Estatísticas gerais (111/831 = 13.4%)
3. ✅ Exemplos de cada tipo (com/sem gestor)
4. ✅ Exportação para Google Sheets com nova coluna
5. ✅ Verificação de que campo NULL é normal

### Casos de Teste

```
Posição 1178:
  Gestor: "Lidiane Pereira" ✅

Posição 1543:
  Gestor: "Rafael Bretas" ✅

Posição 1546:
  Gestor: NULL (esperado - campo não preenchido) ✅
```

## Possibilidades Futuras

1. ⏳ **Usar `manager_id` para enriquecer dados:**
   - Criar endpoint/sincronização de managers
   - Fazer JOIN com tabela de managers
   - Adicionar campos: manager_email, manager_phone, etc.

2. ⏳ **Análises por gestor:**
   - Quantas vagas cada gestor tem
   - Performance por gestor (SLA, taxa de contratação)
   - Vagas abertas por gestor

3. ⏳ **Padronizar preenchimento:**
   - Sugerir preenchimento obrigatório do campo gestor
   - Validação no momento da criação da vaga
   - Importar gestores de sistemas clientes

## Status

✅ **CONCLUÍDO E VALIDADO**

- Data de Implementação: 2026-02-06
- Tipo: Nova Funcionalidade (Adição de Campo)
- Prioridade: Média
- Status: Aplicado em Produção
- Exportação: Concluída
- Migration: `025_add_gestor_field_to_view.sql`

---

**Resumo:** Campo "Gestor" agora está visível na view de análise de posições, extraído dos custom_fields das vagas. 111 posições (13.4%) têm esse campo preenchido. Exportação atualizada com 30 colunas.
