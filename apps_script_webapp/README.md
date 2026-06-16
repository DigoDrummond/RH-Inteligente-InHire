# 🌐 Web App - Sistema de Consulta de Posições InHire

## 🚨 DASHBOARD EM BRANCO? LEIA PRIMEIRO!

**➡️ [`SOLUCAO_DEFINITIVA.md`](SOLUCAO_DEFINITIVA.md) - Guia completo para corrigir dashboard em branco**

---

## 📋 Descrição

Sistema web independente para consulta e análise de posições do processo seletivo InHire.

**Portal Enterprise v2.0** com design profissional e funcionalidades completas.

**Acesso via URL própria** - não precisa abrir a planilha!

---

## ✨ Funcionalidades

### 📊 Dashboard
- **Filtros dinâmicos** (Cliente, Torre, Status)
- Estatísticas principais (total, abertas, contratadas, SLA)
- **Status das Posições** (gráfico de barras horizontal)
- Top 5 clientes
- **Distribuição por SLA** (0-30, 31-60, 61-90, 91-120, 120+ dias)
- **Tabela completa** com 50 posições (9 colunas)
- Distribuição por torre

### 🔍 Busca Avançada ✅ FUNCIONAL
- Filtros por cliente, recrutadora, status, torre
- Tabela de resultados interativa
- Até 100 resultados por busca
- Busca funcional com google.script.run

### 📈 Relatórios ✅ FUNCIONAL
- Resumo executivo com estatísticas
- Performance metrics (taxa de conversão, cancelamento)
- Top performers (melhor cliente, melhor recrutadora)
- Exportações (CSV, Excel, PDF) - placeholders implementados

---

## 🚀 Como fazer o deploy

**Leia o guia completo:** [`GUIA_DEPLOY.md`](GUIA_DEPLOY.md)

**Resumo rápido:**
1. Acesse https://script.google.com
2. Crie novo projeto
3. Copie os 5 arquivos (.gs e .html)
4. Deploy → Nova implantação → Web app
5. Copie a URL e compartilhe!

---

## 📁 Estrutura de Arquivos

```
apps_script_webapp/
├── Code.gs                       # Backend com todas as funções
├── Dashboard.html                # Página inicial com filtros
├── Busca.html                    # Página de busca funcional
├── Relatorios.html               # Página de relatórios funcional
├── Styles.html                   # CSS enterprise profissional
├── SOLUCAO_DEFINITIVA.md         # ⭐ Guia de correção dashboard em branco
├── COMO_FAZER_DEPLOY.md          # Guia completo de deploy/atualização
├── DIAGNOSTICO.md                # Troubleshooting detalhado
├── DESIGN_PROFISSIONAL.md        # Documentação do design system
└── README.md                     # Este arquivo
```

---

## 🔧 Configuração

### Planilha de Dados

Arquivo `Code.gs`, linhas 23-26:

```javascript
const CONFIG = {
  SPREADSHEET_ID: '1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0',
  SHEET_NAME: 'Posições_API',
  APP_NAME: 'Sistema de Consulta de Posições - InHire',
  VERSION: '2.0.0'
};
```

**⚠️ IMPORTANTE:**
- `SPREADSHEET_ID`: ID da planilha com os dados
- `SHEET_NAME`: Nome da aba (padrão: 'Posições_API')

---

## 🎨 Personalização

### Cores do tema

Arquivo `Styles.html`:
```css
/* Gradiente principal */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Nome da aplicação

Arquivo `Code.gs`:
```javascript
APP_NAME: 'Seu Nome Aqui',
```

Arquivos HTML (navegação):
```html
<h1>📊 Seu Nome Dashboard</h1>
```

---

## 🔒 Segurança e Acesso

### Opções de acesso ao deploy:

1. **Somente eu**: Apenas você pode acessar
2. **Qualquer pessoa na organização**: Requer login do Google Workspace
3. **Qualquer pessoa**: Público (não recomendado para dados sensíveis)

**Recomendado:** Opção 2 (organização)

---

## 📊 Fonte de Dados

Os dados vêm da planilha **Posições_API** que é alimentada pelo script:
- `upload_analise_posicoes_to_sheets.py`

Para atualizar os dados:
```bash
python upload_analise_posicoes_to_sheets.py
```

O Web App sempre mostra os dados mais recentes da planilha!

---

## 🐛 Troubleshooting

### ⚠️ Dashboard em branco / Não funciona

**➡️ LEIA: [`SOLUCAO_DEFINITIVA.md`](SOLUCAO_DEFINITIVA.md)**

Solução em 4 passos:
1. Verificar se Code.gs foi atualizado (buscar "getStatusDistribuicao")
2. Copiar Code.gs completo do guia
3. Criar **Nova versão** da implantação (CRÍTICO!)
4. Testar em janela anônima

### Busca não funciona

Verifique:
- ✅ Função `buscarPosicoes(filtros)` existe no Code.gs
- ✅ Deployment foi atualizado para nova versão
- ✅ Cache do navegador foi limpo

### Relatórios não funcionam

Verifique:
- ✅ Função `getDashboardData()` retorna dados corretos
- ✅ Deployment foi atualizado para nova versão
- ✅ Teste em janela anônima

### Dados não aparecem
- Verifique SPREADSHEET_ID no Code.gs
- Verifique se a aba 'Posições_API' existe
- Rode o script: `python upload_analise_posicoes_to_sheets.py`

### Erro de autorização
- Refaça o deploy com nova versão
- Autorize novamente o acesso
- Verifique permissões da planilha

---

## 🔄 Atualizações

Para atualizar o Web App após mudanças no código:

1. Edite os arquivos no Apps Script
2. Deploy → Gerenciar implantações
3. Editar → Nova versão
4. A URL permanece a mesma!

---

## 📱 Responsividade

O Web App é **totalmente responsivo**:
- ✅ Desktop (1920px+)
- ✅ Laptop (1366px)
- ✅ Tablet (768px)
- ✅ Mobile (375px)

---

## 🎯 Roadmap

### v2.0 (Atual) ✅
- ✅ Dashboard com filtros dinâmicos (Cliente, Torre, Status)
- ✅ Gráfico Status das Posições (barras horizontais)
- ✅ Distribuição SLA por faixas (0-30, 31-60, etc.)
- ✅ Tabela completa com 50 posições
- ✅ Busca avançada FUNCIONAL
- ✅ Relatórios FUNCIONAL com resumo executivo
- ✅ Design enterprise profissional
- ✅ Sidebar com branding Framework
- ✅ Paleta de cores #573167
- ✅ Totalmente responsivo

### v2.1 (Próximo)
- ⬜ Exportação real para CSV
- ⬜ Exportação real para Excel
- ⬜ Exportação de relatório PDF
- ⬜ Gráficos interativos (Chart.js)
- ⬜ Filtros por data no dashboard

### v3.0 (Futuro)
- ⬜ Autenticação por usuário
- ⬜ Dashboards personalizáveis
- ⬜ Alertas e notificações
- ⬜ Integração com Power BI/Looker

---

## 📞 Contato

**Desenvolvido por:** Framework Data
**Versão:** 2.0.0 - Enterprise Portal
**Data:** 2026-02-07
**Status:** ✅ Produção

---

## 📝 Changelog

### v2.0 (07/02/2026)
- ✅ Filtros dinâmicos no dashboard
- ✅ Gráfico de Status (barras horizontais)
- ✅ Distribuição SLA por faixas
- ✅ Tabela completa (50 posições, 9 colunas)
- ✅ Busca funcional
- ✅ Relatórios funcional
- ✅ Design enterprise profissional
- ✅ Sidebar Framework branding
- ✅ Paleta #573167

### v1.0 (06/02/2026)
- Dashboard básico
- Navegação entre páginas
- Design inicial

---

## 📄 Licença

Uso interno - Framework Data / InHire

---

**🎉 Portal Enterprise v2.0 - Pronto para uso!**

**Problemas?** Leia: [`SOLUCAO_DEFINITIVA.md`](SOLUCAO_DEFINITIVA.md)
