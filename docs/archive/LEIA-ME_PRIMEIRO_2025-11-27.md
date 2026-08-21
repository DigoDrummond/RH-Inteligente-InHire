# 👋 LEIA-ME PRIMEIRO

## Bem-vindo à Documentação InHire Sync

Esta documentação foi criada em **2025-11-27** e contém informações completas sobre o sistema de sincronização do InHire.

---

## 🚀 Início Rápido

### Se você quer...

#### 📊 **Entender o que foi feito hoje**
👉 Leia: **RESUMO_SESSAO_2025-11-27.md** (5 minutos)

#### 🔍 **Verificar se os dados estão corretos**
👉 Execute:
```bash
python verificar_funil_completo.py
```

#### 📈 **Gerar análises do funil**
👉 Execute:
```bash
python analise_funil_kanban.py
```

#### 🔄 **Sincronizar novos dados**
👉 Execute:
```bash
python sync_inhire.py
```

#### 🛠️ **Corrigir um problema**
👉 Consulte: **SCRIPTS_ANALISE_CORRECAO.md** → Seção "Troubleshooting"

---

## 📚 Guia da Documentação

### 🎯 Sumário Executivo
**RESUMO_SESSAO_2025-11-27.md**
- O que foi feito
- Números principais
- Issues conhecidas
- Como continuar

**Tempo de leitura:** 5 minutos
**Quando ler:** Sempre, para entender o contexto

---

### 📝 Detalhamento Completo
**CHANGELOG_2025-11-27.md**
- Mudanças técnicas detalhadas
- Problemas identificados e soluções
- Resultado da verificação do funil
- Próximos passos

**Tempo de leitura:** 15 minutos
**Quando ler:** Para entender detalhes técnicos

---

### 📊 Estado Atual
**STATUS_ATUAL.md**
- Estatísticas do banco
- Integridade dos dados
- Issues conhecidas
- Scripts disponíveis
- Próximas ações

**Tempo de leitura:** 10 minutos
**Quando ler:** Para health check do sistema

---

### 📘 Guia de Scripts
**SCRIPTS_ANALISE_CORRECAO.md**
- Descrição de todos os scripts
- Como usar cada um
- Workflows típicos
- Troubleshooting completo

**Tempo de leitura:** 20 minutos
**Quando ler:** Antes de usar um script novo

---

### 💻 Referência de Comandos
**COMANDOS_UTEIS.md**
- Comandos SQL úteis
- Scripts bash/PowerShell
- Queries de análise
- Workflows automatizados

**Tempo de leitura:** 5-10 minutos (consulta)
**Quando ler:** Para referência rápida

---

### 🗂️ Índice
**INDICE_DOCUMENTACAO.md**
- Mapa completo da documentação
- Estrutura de arquivos
- Quick reference

**Tempo de leitura:** 5 minutos
**Quando ler:** Para navegar a documentação

---

## 📊 O Que Foi Feito Hoje (TL;DR)

### ✅ Implementado

**Recomendação 5: Link talento_id**
- 75,792 candidaturas verificadas
- 74,462 (99.6%) corrigidas ✅
- 330 (0.4%) órfãs ⚠️

**Recomendação 1: Padronização de etapas**
- 32 → 14 nomes únicos ✅
- 5,317 registros atualizados ✅

**Verificação do Funil**
- Funil validado ✅
- 2 issues identificadas ⚠️
- Métricas documentadas ✅

---

## 🎯 Números Principais

```
Base de Dados:
├─ 75,792 candidaturas
├─ 53,270 talentos
├─ 1,099 vagas
└─ 545 posições

Integridade:
├─ 99.6% candidaturas linkadas ✅
├─ 0.4% órfãs ⚠️
└─ 14 etapas padronizadas ✅

Distribuição do Funil:
├─ Inscrição: 68.21%
├─ Hunting: 16.47%
└─ Outras: 15.32%
```

---

## ⚠️ Issues Conhecidas

### 1. Candidaturas Órfãs (330 - 0.4%)
**O que é:** Candidaturas sem talento_id vinculado
**Impacto:** Baixo (0.4% dos dados)
**Ação:** Investigar se talentos foram deletados

### 2. Etapas com Ordens Múltiplas (8 etapas)
**O que é:** Mesma etapa em diferentes posições do funil
**Causa:** Comportamento intencional da API (cada vaga tem seu funil)
**Ação:** Aceitar OU criar view com ordem canônica

### 3. Sync Talentos Falhando
**O que é:** Erro `url NOT NULL` em talento_arquivos
**Ação:** Re-aplicar migration:
```bash
psql -U postgres -d inhire -c "ALTER TABLE talento_arquivos ALTER COLUMN url DROP NOT NULL;"
```

---

## 🚦 Próximos Passos

### Imediato ⚡
1. Re-aplicar migration para talento_arquivos
2. Re-executar sync de talentos

### Curto Prazo 📅
3. Investigar 330 candidaturas órfãs
4. Análises específicas do funil

### Médio Prazo 📆
5. Decidir sobre normalização de ordens
6. Investigar posições órfãs

---

## 🛠️ Comandos Essenciais

```bash
# Verificar integridade
python verificar_funil_completo.py

# Sincronizar dados
python sync_inhire.py

# Corrigir FK talento_id
python fix_candidatura_talento_id.py

# Padronizar nomes
python padronizar_stage_names_fixed.py

# Análise do funil
python analise_funil_kanban.py

# Análise de diversidade
python analise_diversidade.py
```

---

## 📂 Estrutura de Arquivos

```
G:\Meu Drive\Framework_Data\Inhire\
│
├─ 📄 LEIA-ME_PRIMEIRO.md             ← VOCÊ ESTÁ AQUI
│
├─ 📋 Documentação Principal
│  ├─ RESUMO_SESSAO_2025-11-27.md    ← Comece por aqui
│  ├─ CHANGELOG_2025-11-27.md         ← Detalhes técnicos
│  ├─ STATUS_ATUAL.md                 ← Estado do sistema
│  ├─ SCRIPTS_ANALISE_CORRECAO.md     ← Guia de scripts
│  ├─ COMANDOS_UTEIS.md               ← Referência rápida
│  └─ INDICE_DOCUMENTACAO.md          ← Mapa completo
│
├─ 🔧 Scripts de Correção
│  ├─ fix_candidatura_talento_id.py
│  └─ padronizar_stage_names_fixed.py
│
├─ 📊 Scripts de Análise
│  ├─ verificar_funil_completo.py     ⭐ Mais importante
│  ├─ analise_funil_kanban.py
│  ├─ identificar_variacoes_stage.py
│  └─ analise_diversidade.py
│
└─ 🔄 Scripts de Sincronização
   ├─ sync_inhire.py
   └─ [outros scripts de sync]
```

---

## 🎓 Tutoriais Rápidos

### Tutorial 1: Primeira Verificação
```bash
# 1. Verificar integridade
python verificar_funil_completo.py

# 2. Ler o output
# - Procure por "VERIFICACOES CONCLUIDAS"
# - Veja "RECOMENDACOES"

# 3. Se houver issues, leia SCRIPTS_ANALISE_CORRECAO.md
```

### Tutorial 2: Sincronização Diária
```bash
# 1. Backup (recomendado)
pg_dump -U postgres -d inhire > backup_$(date +%Y%m%d).sql

# 2. Sync
python sync_inhire.py

# 3. Correções automáticas
python fix_candidatura_talento_id.py
python padronizar_stage_names_fixed.py

# 4. Verificar resultado
python verificar_funil_completo.py
```

### Tutorial 3: Análise para Relatório
```bash
# 1. Análise do funil
python analise_funil_kanban.py > relatorio_funil.txt

# 2. Análise de diversidade
python analise_diversidade.py > relatorio_diversidade.txt

# 3. Exportar para Excel (opcional)
# - Abrir relatorio_*.txt
# - Copiar tabelas para Excel
```

---

## 🆘 Precisa de Ajuda?

### Problemas Comuns

**Script não executa**
```bash
# Verificar Python
python --version

# Verificar dependências
pip install -r requirements.txt
```

**Erro de encoding (�)**
```bash
# Configurar UTF-8
set PYTHONIOENCODING=utf-8  # Windows
export PYTHONIOENCODING=utf-8  # Linux/Mac
```

**Banco não conecta**
```bash
# Testar conexão
psql -U postgres -d inhire -c "SELECT 1;"
```

**Mais problemas?**
👉 Consulte: **SCRIPTS_ANALISE_CORRECAO.md** → Seção "Troubleshooting"

---

## 📞 Informações de Contato

**Banco de Dados:** PostgreSQL `inhire` @ localhost:5432
**API:** https://api.inhire.app
**Última atualização:** 2025-11-27 21:10 BRT
**Próxima verificação:** Após próxima sync completa

---

## ✅ Checklist: Estou Pronto?

Antes de começar, verifique se você tem:

- [ ] PostgreSQL instalado e rodando
- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Acesso ao banco `inhire`
- [ ] Credenciais da API InHire configuradas
- [ ] Leu pelo menos o **RESUMO_SESSAO_2025-11-27.md**

---

## 🎯 Recomendações

### Para Desenvolvedores
1. Comece com **RESUMO_SESSAO_2025-11-27.md**
2. Leia **SCRIPTS_ANALISE_CORRECAO.md** antes de rodar scripts
3. Execute `verificar_funil_completo.py` para health check
4. Consulte **COMANDOS_UTEIS.md** para referência rápida

### Para Analistas
1. Leia **RESUMO_SESSAO_2025-11-27.md**
2. Execute `analise_funil_kanban.py` para relatórios
3. Use queries SQL de **COMANDOS_UTEIS.md** para análises ad-hoc
4. Consulte **STATUS_ATUAL.md** para métricas atualizadas

### Para Administradores
1. Leia **STATUS_ATUAL.md** para overview do sistema
2. Implemente workflows de **COMANDOS_UTEIS.md**
3. Configure backups automáticos
4. Monitore issues em **STATUS_ATUAL.md**

---

**Boa sorte! 🚀**

**Esta documentação foi gerada automaticamente em 2025-11-27.**
**Para dúvidas, consulte os arquivos de referência ou execute os scripts de verificação.**

---

## 📖 Versão da Documentação

**Versão:** 2.0
**Data:** 2025-11-27
**Autor:** Claude Code + Marcos Santiago
**Status:** ✅ Completa e Atualizada
