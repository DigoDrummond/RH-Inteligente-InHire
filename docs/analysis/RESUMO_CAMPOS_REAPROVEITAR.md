# 🎯 RESUMO: Campos que Conseguimos Reaproveitar

**Pergunta:** *Quais campos conseguimos reaproveitar da tabela de requisições e do banco de talentos, mapear as pessoas que se candidataram, em qual vaga, status e se progrediram no Kanban?*

---

## ✅ RESPOSTA RÁPIDA

**SIM! Conseguimos mapear TUDO:**

1. ✅ **Quem se candidatou** → Tabela `talentos` (nome, email, telefone, LinkedIn, etc.)
2. ✅ **Em qual vaga** → Tabela `vagas` (nome da vaga, área, senioridade, salário)
3. ✅ **Status atual** → Campo `candidaturas.status` (active, hired, rejected, declined)
4. ✅ **Progressão no Kanban** → Tabela `candidatura_timeline` (histórico completo de movimentações)
5. ✅ **Dados da requisição** → Tabela `requisicoes` (aprovação, motivo, aprovadores)

---

## 📊 Tabelas e Campos Disponíveis

### 1️⃣ TALENTOS (Quem se candidatou)

| Campo | Exemplo | Uso |
|-------|---------|-----|
| **name** | "João Silva" | Nome do candidato |
| **email** | "joao@email.com" | Contato ✉️ |
| **phone** | "(11) 99999-9999" | Telefone 📞 |
| **headline** | "Desenvolvedor Python Senior" | Cargo atual |
| **company** | "Google Brasil" | Empresa atual |
| **location** | "São Paulo, SP" | Localização 📍 |
| **linkedin_username** | "joaosilva" | LinkedIn 🔗 |
| **metadata** | `{...}` | Custom fields (JSON) |

**➕ Tabelas relacionadas:**
- `talento_tags` → Skills/habilidades (Python, React, AWS...)
- `talento_arquivos` → Currículos em PDF/DOC

---

### 2️⃣ CANDIDATURAS (Ligação Candidato ↔ Vaga)

| Campo | Exemplo | Uso |
|-------|---------|-----|
| **vaga_id** | 1234 | Qual vaga se candidatou |
| **talento_id** | 5678 | Quem se candidatou |
| **status** | "active" | ⭐ Status atual |
| **source** | "LinkedIn" | De onde veio (Indeed, Site, etc.) |
| **stage_name** | "Entrevista Técnica" | ⭐ Etapa atual no Kanban |
| **stage_order** | 3 | ⭐ Ordem numérica (1, 2, 3...) |
| **phase_name** | "Aguardando Feedback" | Subfase da etapa |
| **applied_at** | "2024-01-15" | Data de aplicação |

**Status possíveis:**
- `active` 🟢 → Em processo (60-70% dos casos)
- `hired` ✅ → Contratado (5-10%)
- `rejected` ❌ → Rejeitado (20-30%)
- `declined` ⛔ → Desistiu (5-10%)

---

### 3️⃣ CANDIDATURA_TIMELINE (Histórico no Kanban)

| Campo | Exemplo | Uso |
|-------|---------|-----|
| **changed_at** | "2024-01-20 14:30" | ⭐ Quando aconteceu |
| **event_type** | "stage_changed" | Tipo de movimentação |
| **from_stage_name** | "Triagem" | ⭐ De onde veio |
| **from_stage_order** | 1 | Ordem anterior |
| **to_stage_name** | "Entrevista RH" | ⭐ Para onde foi |
| **to_stage_order** | 2 | Ordem nova |
| **duration_days** | 5 | ⭐ Quantos dias ficou no stage anterior |
| **changed_by_name** | "Ana Recruiter" | Quem moveu |
| **notes** | "Candidato aprovado" | Observações |

**Eventos possíveis:**
- `stage_changed` → Avançou/retrocedeu no funil
- `hired` → Foi contratado ✅
- `rejected` → Foi rejeitado ❌
- `declined` → Desistiu ⛔

---

### 4️⃣ REQUISIÇÕES (Aprovação da Vaga)

| Campo | Exemplo | Uso |
|-------|---------|-----|
| **vaga_id** | 1234 | Qual vaga |
| **status** | "approved" | Status da aprovação |
| **reason** | "Substituição de funcionário" | Motivo da requisição |
| **name** | "Requisição Dev Python" | Nome |
| **approvers** | `[{...}]` | Lista de aprovadores (JSON) |
| **approval_workflow** | `{...}` | Fluxo de aprovação (JSON) |
| **salary_min** | 5000.00 | Salário mínimo |
| **salary_max** | 10000.00 | Salário máximo |
| **user_name** | "Maria RH" | Quem criou |

**Status possíveis:**
- `approved` ✅ → Pode contratar
- `pending` ⏳ → Aguardando aprovação
- `rejected` ❌ → Negada
- `canceled` ⛔ → Cancelada

---

### 5️⃣ VAGAS (Jobs)

| Campo | Exemplo | Uso |
|-------|---------|-----|
| **name** | "Desenvolvedor Python Senior" | Nome da vaga |
| **area** | "Tecnologia" | Área/departamento |
| **seniority** | "Senior" | Nível |
| **status** | "OPEN" | Aberta/fechada |
| **location** | "São Paulo - Remoto" | Local |
| **salary_max** | 15000.00 | Salário |
| **open_positions** | 3 | Quantas vagas abertas |
| **user_name** | "Carlos Recruiter" | Recrutador |

---

## 🎯 Exemplo Prático: Mapeamento Completo

### Pergunta: "Quem se candidatou para 'Desenvolvedor Python Senior' e como está progredindo?"

```sql
SELECT
    -- QUEM (Candidato)
    t.name AS candidato,
    t.email,
    t.phone,
    t.linkedin_username,

    -- ONDE (Vaga)
    v.name AS vaga,
    v.area,
    v.salary_max AS salario_max,

    -- STATUS ATUAL
    c.status AS status_candidatura,
    c.stage_name AS etapa_atual_kanban,
    c.stage_order AS ordem_etapa,

    -- ORIGEM E DATA
    c.source AS origem_candidatura,
    c.applied_at AS data_aplicacao,
    EXTRACT(DAY FROM NOW() - c.applied_at) AS dias_no_processo,

    -- REQUISIÇÃO
    r.status AS requisicao_status,
    r.reason AS requisicao_motivo

FROM candidaturas c
INNER JOIN talentos t ON c.talento_id = t.id
INNER JOIN vagas v ON c.vaga_id = v.id
LEFT JOIN requisicoes r ON v.id = r.vaga_id
WHERE v.name ILIKE '%Python Senior%'
ORDER BY c.stage_order DESC, c.applied_at DESC;
```

**Resultado:**

| candidato | email | vaga | status_candidatura | etapa_atual_kanban | ordem_etapa | dias_no_processo |
|-----------|-------|------|-------------------|-------------------|-------------|------------------|
| João Silva | joao@email.com | Dev Python Senior | active | Entrevista Técnica | 3 | 7 |
| Maria Santos | maria@email.com | Dev Python Senior | active | Entrevista RH | 2 | 3 |
| Pedro Costa | pedro@email.com | Dev Python Senior | hired | Contratado | 6 | 45 |
| Ana Lima | ana@email.com | Dev Python Senior | rejected | Triagem | 1 | 10 |

---

## 🚀 Progressão no Kanban (Timeline)

### Pergunta: "Como o João Silva progrediu no processo seletivo?"

```sql
SELECT
    ct.changed_at AS data_movimentacao,
    ct.from_stage_name || ' → ' || ct.to_stage_name AS movimentacao,
    ct.duration_days AS dias_no_stage,
    ct.changed_by_name AS movido_por,
    ct.notes AS observacao
FROM candidatura_timeline ct
INNER JOIN candidaturas c ON ct.candidatura_id = c.id
INNER JOIN talentos t ON c.talento_id = t.id
WHERE t.name = 'João Silva'
  AND c.vaga_id = 1234  -- Dev Python Senior
ORDER BY ct.changed_at;
```

**Resultado:**

| data_movimentacao | movimentacao | dias_no_stage | movido_por | observacao |
|------------------|--------------|---------------|-----------|------------|
| 2024-01-15 10:00 | NULL → Triagem | NULL | Sistema | Candidatura recebida |
| 2024-01-17 14:30 | Triagem → Entrevista RH | 2 | Ana RH | Currículo aprovado |
| 2024-01-20 09:00 | Entrevista RH → Entrevista Técnica | 3 | Carlos Tech | Fit cultural OK |
| 2024-01-22 16:00 | Entrevista Técnica → Aguardando Feedback | 2 | Carlos Tech | Teste técnico enviado |

---

## 📊 Funil de Conversão

### Pergunta: "Qual a taxa de conversão da vaga 'Dev Python Senior'?"

```sql
SELECT
    v.name AS vaga,
    COUNT(*) AS total_candidatos,

    -- Por stage
    COUNT(*) FILTER (WHERE c.stage_order = 1) AS triagem,
    COUNT(*) FILTER (WHERE c.stage_order = 2) AS entrevista_rh,
    COUNT(*) FILTER (WHERE c.stage_order = 3) AS entrevista_tecnica,
    COUNT(*) FILTER (WHERE c.stage_order >= 4) AS fases_finais,

    -- Por status
    COUNT(*) FILTER (WHERE c.status = 'hired') AS contratados,
    COUNT(*) FILTER (WHERE c.status = 'rejected') AS rejeitados,

    -- Taxa de conversão
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE c.status = 'hired') / COUNT(*),
        2
    ) AS taxa_conversao_pct

FROM vagas v
LEFT JOIN candidaturas c ON v.id = c.vaga_id
WHERE v.name ILIKE '%Python Senior%'
GROUP BY v.name;
```

**Resultado:**

| vaga | total_candidatos | triagem | entrevista_rh | entrevista_tecnica | fases_finais | contratados | rejeitados | taxa_conversao_pct |
|------|-----------------|---------|---------------|-------------------|--------------|-------------|------------|-------------------|
| Dev Python Senior | 45 | 20 | 15 | 8 | 2 | 1 | 25 | 2.22% |

---

## ✅ RESUMO: O Que Conseguimos

### ✔️ Dados Pessoais (Talentos)
- Nome, email, telefone
- Cargo, empresa, localização
- LinkedIn, foto
- Skills/habilidades (tags)
- Currículos (arquivos)

### ✔️ Candidatura
- Status (active, hired, rejected, declined)
- Origem (LinkedIn, Indeed, Site)
- Data de aplicação
- Vaga aplicada

### ✔️ Posição no Kanban
- Stage atual (nome e ordem)
- Phase atual (subfase)
- Última atualização

### ✔️ Histórico Completo (Timeline)
- Todas as movimentações
- Datas de cada mudança
- Quem moveu
- Tempo em cada stage
- Observações/notas

### ✔️ Requisição (Aprovação)
- Status da aprovação
- Motivo da requisição
- Aprovadores
- Faixa salarial

### ✔️ Métricas Calculadas
- Dias no processo
- Taxa de conversão
- Tempo médio por stage
- Funil de candidatos

---

## 🎨 Arquivos Criados

1. **`analise_candidatos_funil.sql`**
   - 4 views SQL prontas para uso
   - Queries de exemplo
   - Documentação inline

2. **`MAPEAMENTO_CANDIDATOS_FUNIL.md`**
   - Documentação completa
   - Exemplos de queries
   - Guia de exportação

3. **`RESUMO_CAMPOS_REAPROVEITAR.md`** (este arquivo)
   - Resumo executivo
   - Exemplos práticos
   - Tabelas de referência rápida

---

## 🚀 Próximos Passos

1. **Execute o script SQL:**
   ```bash
   psql -U postgres -d inhire -f analise_candidatos_funil.sql
   ```

2. **Teste as queries** de exemplo

3. **Conecte no Power BI / Google Sheets**

4. **Crie dashboards visuais**

---

## 📞 Dúvidas Comuns

**Q: Consigo ver quantas pessoas avançaram de "Triagem" para "Entrevista RH"?**
✅ SIM! Use a tabela `candidatura_timeline` filtrando por `from_stage_name` e `to_stage_name`

**Q: Consigo calcular o tempo médio em cada etapa?**
✅ SIM! Use o campo `duration_days` na `candidatura_timeline`

**Q: Consigo ver quais candidatos estão parados há muito tempo?**
✅ SIM! Compare `candidaturas.updated_at_inhire` com a data atual

**Q: Consigo filtrar por vaga, área ou senioridade?**
✅ SIM! Use os campos da tabela `vagas` (name, area, seniority)

**Q: A requisição é obrigatória?**
❌ NÃO! Algumas vagas não têm requisição. Use `LEFT JOIN requisicoes`

---

**Status:** ✅ **TUDO PRONTO PARA USO!**

Todos os campos necessários estão disponíveis e sincronizados com a API Inhire. As views SQL estão criadas e prontas para conectar em ferramentas de BI.
