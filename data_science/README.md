# 📊 Projeto de Ciência de Dados - Inhire

**Data de Criação:** 2026-03-05
**Status:** Em Desenvolvimento (Fase 1)
**Duração Estimada:** 12 semanas

---

## 🎯 Objetivos do Projeto

1. **Prever tempo de contratação** - Estimar dias para preencher vagas com base em características
2. **Prever conversão de candidatos** - Identificar candidatos com maior probabilidade de contratação
3. **Otimizar funil de recrutamento** - Identificar gargalos e oportunidades de melhoria

---

## 📁 Estrutura do Projeto

```
data_science/
├── notebooks/              # Jupyter notebooks (análises interativas)
│   ├── 01_setup_conexao.ipynb           ✅ CRIADO
│   ├── 02_eda_vagas_posicoes.ipynb      ⏳ Pendente
│   ├── 03_eda_candidaturas_funil.ipynb  ⏳ Pendente
│   ├── 04_feature_engineering.ipynb     ⏳ Pendente
│   ├── 05_modelo_tempo_contratacao.ipynb
│   ├── 06_modelo_conversao_candidatos.ipynb
│   ├── 07_analise_funil_otimizacao.ipynb
│   └── 08_correlacoes_insights.ipynb
│
├── scripts/                # Scripts Python automatizados
│   ├── extract_datasets.py
│   ├── train_models.py
│   └── predict.py
│
├── models/                 # Modelos treinados (.pkl)
│
├── dashboards/             # Dashboards interativos (Streamlit)
│   └── app_streamlit.py
│
├── data/                   # Dados processados
│   └── datasets_preparados/
│
├── docs/                   # Documentação
│   └── GUIA_CIENCIA_DADOS.md
│
├── requirements.txt        # Dependências Python ✅ CRIADO
├── config_ds.py           # Configurações do projeto ✅ CRIADO
└── README.md              # Este arquivo
```

---

## 🚀 Primeiros Passos

### 1. Instalar Dependências

**Recomendado:** Criar um ambiente virtual primeiro

```bash
# Navegar até a pasta data_science
cd "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire\data_science"

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows)
venv\Scripts\activate

# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt
```

**Tempo estimado:** 5-10 minutos

### 2. Verificar Instalação

```bash
# Testar configurações
python config_ds.py
```

**Saída esperada:**
```
[OK] Diretorios criados/verificados com sucesso!
================================================================================
CONFIGURAÇÃO DO PROJETO DE CIÊNCIA DE DADOS - INHIRE
================================================================================
Base Directory:       ...
Database:             inhire@localhost:5432
Random State:         42
Test Size:            20.0%
CV Folds:             5
================================================================================
[OK] Conexao com PostgreSQL OK!
```

### 3. Configurar Jupyter

```bash
# Instalar kernel do Jupyter com o nome do projeto
python -m ipykernel install --user --name=inhire_ds --display-name="Inhire DS"

# Iniciar JupyterLab
jupyter lab
```

**Abrir em:** http://localhost:8888

### 4. Começar pelos Notebooks

**Ordem recomendada:**

1. **📘 01_setup_conexao.ipynb** ✅ CRIADO
   - Configurar ambiente e conexão
   - Explorar estrutura do banco
   - Criar funções helper

2. **📘 02_eda_vagas_posicoes.ipynb** (Próximo)
   - Análise exploratória de vagas
   - Visualizações e estatísticas
   - Identificar padrões

3. **📘 03_eda_candidaturas_funil.ipynb**
   - Análise do funil de candidaturas
   - Taxas de conversão
   - Identificar gargalos

4. **E assim por diante...**

---

## 📚 Recursos para Iniciantes

### Conceitos Básicos

- **DataFrame** = Tabela de dados (como Excel)
- **SQL** = Linguagem para consultar bancos de dados
- **Machine Learning** = Algoritmos que aprendem padrões dos dados
- **Feature** = Variável/coluna usada para prever algo
- **Target** = Variável que queremos prever

### Tutoriais Recomendados

**Python & Pandas:**
- [Pandas em 10 minutos](https://pandas.pydata.org/docs/user_guide/10min.html)
- [Real Python - Pandas Tutorial](https://realpython.com/pandas-python-explore-dataset/)

**Machine Learning:**
- [Kaggle Learn - Intro to Machine Learning](https://www.kaggle.com/learn/intro-to-machine-learning)
- [Scikit-Learn Tutorial](https://scikit-learn.org/stable/tutorial/index.html)

**SQL:**
- [W3Schools SQL](https://www.w3schools.com/sql/)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)

---

## 📊 Dados Disponíveis

Com base na análise do banco de dados Inhire, temos:

| Tabela | Registros | Descrição |
|--------|-----------|-----------|
| **candidatura_timeline** | 134,285 | Histórico de transições no funil |
| **candidaturas** | 85,664 | Aplicações de talentos às vagas |
| **talentos** | 59,884 | Base de candidatos |
| **vaga_tags** | 12,294 | Tags das vagas |
| **position_timeline** | 3,654 | Histórico de mudanças de posições |
| **posicoes** | 1,439 | Posições dentro de vagas |
| **vagas** | 1,212 | Vagas/Jobs |
| **requisicoes** | 892 | Requisições de aprovação |
| **clientes** | 76 | Clientes do tenant |

**Total:** ~300.000 registros

---

## 🎯 Métricas de Sucesso

### Modelo 1: Tempo de Contratação
- ✅ R² > 0.6 (60% da variância explicada)
- ✅ MAE < 5 dias (erro médio absoluto)

### Modelo 2: Conversão de Candidatos
- ✅ ROC-AUC > 0.75
- ✅ Precision > 0.6 para top 10% candidatos

### Análise de Funil
- ✅ Identificar 3+ gargalos acionáveis
- ✅ Recomendações que reduzam 10% do tempo médio

---

## ⚠️ Troubleshooting

### Erro ao instalar psycopg2:
```bash
# Usar versão binária (já incluída no requirements.txt)
pip install psycopg2-binary
```

### Erro ao instalar XGBoost/SHAP:
```bash
# Requer Microsoft Visual C++ 14.0+
# Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### Jupyter não abre:
```bash
# Reinstalar Jupyter
pip uninstall jupyter jupyterlab
pip install jupyter jupyterlab
```

### Erro de encoding no Windows:
```bash
# Configurar encoding UTF-8
set PYTHONIOENCODING=utf-8
```

---

## 📅 Cronograma (12 Semanas)

### ✅ **Fase 1: Fundação (Semanas 1-2)** - EM ANDAMENTO
- [x] Estrutura de pastas
- [x] requirements.txt
- [x] config_ds.py
- [x] Notebook 01: Setup e Conexão
- [ ] Notebook 02: EDA Vagas
- [ ] Notebook 03: EDA Funil

### ⏳ **Fase 2: Feature Engineering (Semanas 3-4)**
- [ ] Notebook 04: Feature Engineering
- [ ] Script extract_datasets.py

### ⏳ **Fase 3: Modelos Preditivos (Semanas 5-8)**
- [ ] Notebook 05: Modelo Tempo Contratação
- [ ] Notebook 06: Modelo Conversão

### ⏳ **Fase 4: Análise de Funil (Semanas 9-10)**
- [ ] Notebook 07: Análise Funil
- [ ] Notebook 08: Correlações

### ⏳ **Fase 5: Dashboard (Semanas 11-12)**
- [ ] Dashboard Streamlit
- [ ] Scripts de automação
- [ ] Documentação final

---

## 🤝 Suporte

Para dúvidas ou problemas:
1. Consultar notebooks (têm explicações detalhadas)
2. Consultar GUIA_CIENCIA_DADOS.md (quando criado)
3. Verificar referências e tutoriais acima

---

## 📝 Notas Importantes

- **Ambiente Virtual:** Sempre ative o ambiente virtual antes de trabalhar
  ```bash
  venv\Scripts\activate  # Windows
  ```

- **Kernel do Jupyter:** Sempre selecione o kernel "Inhire DS" nos notebooks

- **Commits Git:** NÃO commitar arquivos grandes:
  - ❌ `models/*.pkl` (modelos treinados)
  - ❌ `data/datasets_preparados/*.csv` (datasets processados)
  - ❌ `venv/` (ambiente virtual)

- **Backup:** Salvar modelos e datasets importantes em local seguro

---

**Última atualização:** 2026-03-05
**Status:** Fase 1 em andamento (4/15 tarefas concluídas)
