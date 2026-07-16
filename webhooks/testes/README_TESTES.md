# Testes Locais - Webhooks Google Sheets

**Objetivo:** Testar TUDO localmente antes de implantar no Apps Script

---

## 🎯 Por Que Testar Antes?

✅ Validar se o token está correto
✅ Verificar se payloads processam corretamente
✅ Simular recebimento de webhooks
✅ Identificar erros ANTES de implantar
✅ Ganhar confiança no código

**Tempo:** 10-15 minutos
**Custo:** R$ 0

---

## 📁 Arquivos de Teste

```
testes/
├── README_TESTES.md              ← Este arquivo
├── 1_testar_token.py             ← TESTE 1: Valida token
├── 2_testar_payload.py           ← TESTE 2: Valida processamento
├── 3_testar_webhook_completo.py  ← TESTE 3: Simula webhook completo
└── executar_todos.py             ← Roda todos os testes
```

---

## 🚀 Como Executar

### Pré-requisito

Python 3.7+ instalado

**Verificar:**
```bash
python --version
```

---

### Opção 1: Executar Teste Individual

```bash
# Teste 1: Validar Token
python webhooks/testes/1_testar_token.py

# Teste 2: Validar Payloads
python webhooks/testes/2_testar_payload.py

# Teste 3: Simulação Completa
python webhooks/testes/3_testar_webhook_completo.py
```

---

### Opção 2: Executar Todos de Uma Vez

```bash
python webhooks/testes/executar_todos.py
```

---

## 📝 TESTE 1: Validação de Token

### O Que Testa

- ✅ Gera token seguro UUID
- ✅ Valida formato do token
- ✅ Testa header Authorization
- ✅ Simula validação de webhook

### Como Executar

```bash
python webhooks/testes/1_testar_token.py
```

### O Que Esperar

```
🔑 SEU TOKEN SECRETO:

   a1b2c3d4-e5f6-7890-abcd-ef1234567890

📋 COPIE ESTE TOKEN E USE NOS TESTES SEGUINTES

✅ Token válido!
✅ VALIDAÇÃO PASSOU!
```

### O Que Fazer

1. Execute o script
2. Escolha gerar novo token OU testar existente
3. **COPIE o token** gerado
4. **GUARDE** para usar nos próximos passos

---

## 📦 TESTE 2: Validação de Payloads

### O Que Testa

- ✅ Processa payloads de 5 tipos de eventos
- ✅ Valida campos obrigatórios
- ✅ Gera linhas para planilha
- ✅ Testa formatação de dados

### Como Executar

```bash
python webhooks/testes/2_testar_payload.py
```

### O Que Esperar

```
🧪 TESTANDO: JOB_TALENT_ADDED

✅ Todos os campos obrigatórios presentes!
✅ PROCESSAMENTO CONCLUÍDO

📊 LINHA QUE SERIA ADICIONADA NA PLANILHA:
Data/Hora           | 25/06/2026 10:30:15
Vaga                | Desenvolvedor Full Stack Senior
Candidato ID        | talent-abc-123
...
```

### O Que Fazer

1. Execute o script
2. Veja como cada payload é processado
3. Verifique se as linhas geradas estão corretas
4. (Opcional) Teste payload customizado

---

## 🔔 TESTE 3: Simulação Completa

### O Que Testa

- ✅ Fluxo completo de webhook
- ✅ Autenticação (token)
- ✅ Parsing de payload
- ✅ Processamento de evento
- ✅ Retorno de resposta
- ✅ Cenários de erro

### Como Executar

```bash
python webhooks/testes/3_testar_webhook_completo.py
```

### Antes de Executar

**IMPORTANTE:** Edite o arquivo e configure seu token:

```python
# Linha 20
CONFIG = {
    "SECRET_TOKEN": "cole-seu-token-aqui",  # ← SUBSTITUA
    "TIMEZONE": "America/Sao_Paulo"
}
```

### O Que Esperar

```
🧪 CENÁRIO 1: Candidatura com token CORRETO

🔔 WEBHOOK RECEBIDO
🔐 ETAPA 1: VALIDAR AUTENTICAÇÃO
   ✅ PASSOU: Token válido!
⚙️  ETAPA 2: PARSEAR PAYLOAD
   ✅ PASSOU: Payload válido!
⚙️  ETAPA 3: PROCESSAR EVENTO
   ✅ PASSOU: Evento processado
📝 ETAPA 4: REGISTRAR LOG
   ✅ Log registrado
✅ ETAPA 5: RETORNAR RESPOSTA
   Código: 200
   Status: success

📊 RESULTADO DO TESTE
   ✅ TESTE PASSOU!
```

### Cenários Testados

1. ✅ Token correto → 200 OK
2. ❌ Token incorreto → 401 Unauthorized
3. ❌ Sem "Bearer" → 401 Unauthorized
4. ❌ Sem header → 401 Unauthorized
5. ❌ Evento desconhecido → 400 Bad Request

---

## ✅ Checklist de Validação

Após executar os testes:

### Teste 1 (Token)
- [ ] Token gerado com sucesso
- [ ] Formato validado (20+ caracteres, sem espaços)
- [ ] Header Authorization correto: `Bearer <token>`
- [ ] Validação de webhook simulada com sucesso

### Teste 2 (Payloads)
- [ ] Todos os 5 tipos de eventos processados
- [ ] Campos obrigatórios presentes
- [ ] Linhas geradas corretamente
- [ ] Formatação de dados OK

### Teste 3 (Webhook Completo)
- [ ] Cenário 1 (token correto) → 200 OK ✅
- [ ] Cenário 2 (token errado) → 401 ❌
- [ ] Cenário 3 (sem Bearer) → 401 ❌
- [ ] Cenário 4 (sem header) → 401 ❌
- [ ] Cenário 5 (evento desconhecido) → 400 ❌

**Se TODOS passaram:** 🎉 **Pronto para Apps Script!**

---

## 🐛 Troubleshooting

### Erro: "Python não encontrado"

**Problema:** Python não está instalado ou no PATH

**Solução:**
1. Instale Python: https://python.org/downloads
2. Durante instalação, marque "Add to PATH"
3. Reinicie terminal
4. Tente novamente

---

### Erro: "ModuleNotFoundError"

**Problema:** Biblioteca não encontrada

**Solução:**
```bash
# Nenhuma lib externa necessária!
# Testes usam apenas bibliotecas padrão do Python
```

Se erro persistir, reinstale Python.

---

### Token está dando erro de validação

**Problema:** Token tem caracteres problemáticos

**Solução:**
1. Execute `1_testar_token.py`
2. Escolha "gerar novo token"
3. Use o token gerado (formato UUID)

---

### Payload não processa

**Problema:** Campos faltando ou formato errado

**Solução:**
1. Execute `2_testar_payload.py`
2. Veja quais campos são obrigatórios
3. Ajuste seu payload

---

## 📊 Exemplo de Execução Completa

```bash
# 1. Gerar e validar token
$ python webhooks/testes/1_testar_token.py
Token gerado: a1b2c3d4-e5f6-7890-abcd-ef1234567890
✅ Token válido!

# 2. Testar processamento de payloads
$ python webhooks/testes/2_testar_payload.py
✅ Teste passou! (5/5 eventos)

# 3. Simular webhook completo
$ python webhooks/testes/3_testar_webhook_completo.py
# (edite CONFIG primeiro com seu token)
✅ TODOS OS TESTES PASSARAM! (5/5 cenários)

# 4. Agora pode ir para Apps Script!
✅ Código validado localmente
✅ Pronto para implantar
```

---

## 🎯 Próximos Passos

Após **TODOS os testes passarem**:

1. ✅ Copie o token gerado
2. ✅ Cole no arquivo `2_setup_planilha.js` (linha 19)
3. ✅ Cole no arquivo `3_webhook_receiver.js` (linha 21)
4. ✅ Prossiga com setup no Apps Script

**Confiança:** 100% que o código vai funcionar! 🚀

---

## ❓ FAQ

**Q: Preciso executar TODOS os testes?**
A: Recomendado! Mas se tiver pouco tempo, execute apenas o Teste 3.

**Q: Posso pular os testes?**
A: Pode, mas não recomendo. Testes economizam tempo depois.

**Q: Testes modificam alguma coisa?**
A: Não! Apenas simulam. Não tocam em arquivos nem API.

**Q: Quanto tempo leva?**
A: 10-15 minutos total para os 3 testes.

**Q: Preciso saber Python?**
A: Não! Só execute os scripts e leia os resultados.

---

**Criado em:** 2026-06-25
**Versão:** 1.0.0
**Status:** ✅ Pronto para uso
