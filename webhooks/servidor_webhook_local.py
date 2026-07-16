"""
Servidor Webhook Local - Inhire
================================

Recebe webhooks REAIS da Inhire e processa localmente
Use para testar ANTES de subir para Apps Script

Como usar:
1. Execute este script: python servidor_webhook_local.py
2. Exponha porta local com ngrok: ngrok http 5000
3. Configure webhooks na Inhire apontando para URL do ngrok
4. Eventos reais da Inhire serao recebidos e processados aqui
5. Valide que tudo funciona
6. Migre logica para Apps Script
"""

from flask import Flask, request, jsonify
import csv
import os
import uuid
from datetime import datetime

# ========================================
# CONFIGURACAO
# ========================================

# Token de seguranca (mesmo que usara no Apps Script)
SECRET_TOKEN = str(uuid.uuid4())

# Diretorio de saida
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "webhooks_recebidos")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Arquivo de log
LOG_FILE = os.path.join(OUTPUT_DIR, "log_webhooks.csv")

# Inicializar Flask
app = Flask(__name__)


# ========================================
# PROCESSADORES (mesma logica do Apps Script)
# ========================================

def processar_candidatura(payload):
    """Processa JOB_TALENT_ADDED"""
    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("jobId", ""),
        payload.get("talentId", ""),
        payload.get("stageName", ""),
        payload.get("source", ""),
        payload.get("linkedinUsername", ""),
        payload.get("location", ""),
        payload.get("targetSalary", ""),
        payload.get("workModel", ""),
        payload.get("userName", "Sistema")
    ]

    salvar_csv("candidaturas.csv", linha, [
        "Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa Inicial",
        "Origem", "LinkedIn", "Localizacao", "Pretensao Salarial",
        "Modelo de Trabalho", "Usuario"
    ])

    return {"success": True, "message": f"Candidatura registrada: {payload.get('jobName')}"}


def processar_mudanca_etapa(payload):
    """Processa JOB_TALENT_STAGE_ADDED"""
    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("talentId", ""),
        payload.get("previousStageName", ""),
        payload.get("stageName", ""),
        payload.get("stageType", ""),
        payload.get("phaseType", ""),
        payload.get("userName", "Sistema")
    ]

    salvar_csv("mudancas_etapa.csv", linha, [
        "Data/Hora", "Vaga", "Candidato ID", "Etapa Anterior",
        "Nova Etapa", "Tipo de Etapa", "Fase", "Usuario"
    ])

    return {"success": True, "message": f"Mudanca registrada: {payload.get('previousStageName')} -> {payload.get('stageName')}"}


def processar_nova_vaga(payload):
    """Processa JOB_ADDED"""
    descricao = payload.get("jobDescription", "")
    if len(descricao) > 200:
        descricao = descricao[:200]

    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("jobId", ""),
        descricao,
        payload.get("userName", "Sistema")
    ]

    salvar_csv("vagas.csv", linha, [
        "Data/Hora", "Nome da Vaga", "Vaga ID", "Descricao", "Criado por"
    ])

    return {"success": True, "message": f"Vaga registrada: {payload.get('jobName')}"}


def processar_formulario(payload):
    """Processa FORM_RESPONSE_ADDED"""
    acertos = payload.get("correctQuestionsCount", 0)
    total = payload.get("totalQuestions", 1)
    percentual = round((acertos / total) * 100, 1) if total > 0 else 0

    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobId", ""),
        payload.get("talentId", ""),
        payload.get("formType", ""),
        payload.get("title", ""),
        "Sim" if payload.get("passed") else "Nao",
        acertos,
        total,
        f"{percentual}%"
    ]

    salvar_csv("formularios.csv", linha, [
        "Data/Hora", "Vaga ID", "Candidato ID", "Tipo", "Titulo",
        "Aprovado?", "Acertos", "Total", "% Acerto"
    ])

    return {"success": True, "message": f"Formulario registrado: {payload.get('title')}"}


def processar_requisicao(payload):
    """Processa REQUISITION_STATUS_UPDATED"""
    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("title", ""),
        payload.get("requisitionId", ""),
        payload.get("oldStatus", ""),
        payload.get("status", ""),
        payload.get("userName", "Sistema")
    ]

    salvar_csv("requisicoes.csv", linha, [
        "Data/Hora", "Titulo", "Requisicao ID", "Status Anterior",
        "Novo Status", "Usuario"
    ])

    return {"success": True, "message": f"Requisicao atualizada: {payload.get('title')}"}


# ========================================
# UTILITARIOS
# ========================================

def salvar_csv(nome_arquivo, linha, colunas):
    """Salva linha em CSV"""
    caminho = os.path.join(OUTPUT_DIR, nome_arquivo)

    # Criar arquivo com cabecalho se nao existir
    if not os.path.exists(caminho):
        with open(caminho, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(colunas)

    # Adicionar linha
    with open(caminho, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(linha)


def registrar_log(evento_tipo, status, payload, erro=None):
    """Registra no log geral"""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Data/Hora", "Tipo de Evento", "Status", "Payload (resumo)", "Erro"])

    with open(LOG_FILE, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        payload_resumo = str(payload)[:500]
        writer.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            evento_tipo,
            status,
            payload_resumo,
            erro or ""
        ])


def validar_autenticacao(auth_header):
    """Valida token de autenticacao"""
    if not auth_header:
        return False

    expected = f"Bearer {SECRET_TOKEN}"
    return auth_header == expected


def identificar_evento(path):
    """Identifica tipo de evento pela URL"""
    if "job-talent-added" in path:
        return "job_talent_added"
    elif "job-talent-stage-added" in path:
        return "job_talent_stage_added"
    elif "job-added" in path:
        return "job_added"
    elif "form-response-added" in path:
        return "form_response_added"
    elif "requisition-status-updated" in path:
        return "requisition_status_updated"
    else:
        return "unknown"


# ========================================
# ROTAS DO SERVIDOR
# ========================================

@app.route('/', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        "service": "Webhook Receiver Local - Inhire",
        "status": "running",
        "version": "1.0.0",
        "token": SECRET_TOKEN,
        "message": "Use POST /<tipo-evento> para enviar webhooks"
    })


@app.route('/<path:evento>', methods=['POST'])
def receber_webhook(evento):
    """Recebe webhook da Inhire"""
    try:
        # 1. Validar autenticacao
        auth_header = request.headers.get('Authorization')

        if not validar_autenticacao(auth_header):
            print(f"ERRO: Autenticacao falhou")
            print(f"   Recebido: {auth_header}")
            print(f"   Esperado: Bearer {SECRET_TOKEN}")
            registrar_log("erro_auth", "failed", {}, "Token invalido")
            return jsonify({"error": "Unauthorized"}), 401

        # 2. Parsear payload
        payload = request.get_json()
        evento_tipo = identificar_evento(evento)

        print()
        print("=" * 70)
        print(f"WEBHOOK RECEBIDO: {evento_tipo}")
        print("=" * 70)
        print(f"Payload: {payload}")
        print()

        # 3. Processar evento
        if evento_tipo == "job_talent_added":
            resultado = processar_candidatura(payload)
        elif evento_tipo == "job_talent_stage_added":
            resultado = processar_mudanca_etapa(payload)
        elif evento_tipo == "job_added":
            resultado = processar_nova_vaga(payload)
        elif evento_tipo == "form_response_added":
            resultado = processar_formulario(payload)
        elif evento_tipo == "requisition_status_updated":
            resultado = processar_requisicao(payload)
        else:
            resultado = {"success": False, "error": "Evento desconhecido"}

        # 4. Registrar log
        registrar_log(
            evento_tipo,
            "success" if resultado.get("success") else "failed",
            payload,
            resultado.get("error")
        )

        # 5. Exibir resultado
        if resultado.get("success"):
            print(f"OK: {resultado['message']}")
        else:
            print(f"ERRO: {resultado.get('error')}")

        print("=" * 70)
        print()

        # 6. Retornar resposta
        return jsonify({
            "status": "success" if resultado.get("success") else "failed",
            "message": resultado.get("message", resultado.get("error")),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"ERRO ao processar webhook: {e}")
        import traceback
        traceback.print_exc()

        registrar_log("erro_geral", "failed", {}, str(e))

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ========================================
# MAIN
# ========================================

if __name__ == '__main__':
    print()
    print("=" * 70)
    print("SERVIDOR WEBHOOK LOCAL - INHIRE")
    print("=" * 70)
    print()
    print("Token de seguranca:")
    print(f"  {SECRET_TOKEN}")
    print()
    print("Header para configurar na Inhire:")
    print(f"  Authorization: Bearer {SECRET_TOKEN}")
    print()
    print("=" * 70)
    print()
    print("PROXIMOS PASSOS:")
    print()
    print("1. Mantenha este servidor rodando")
    print("2. Em outro terminal, execute:")
    print("   ngrok http 5000")
    print()
    print("3. Copie a URL do ngrok (ex: https://abc123.ngrok.io)")
    print()
    print("4. Configure webhooks na Inhire:")
    print("   - URL: https://abc123.ngrok.io/job-talent-added")
    print("   - Header: Authorization: Bearer <TOKEN_ACIMA>")
    print()
    print("5. Faca alguma acao na Inhire (candidatura, etc.)")
    print()
    print("6. Webhook sera recebido e processado aqui!")
    print()
    print("7. Verifique arquivos CSV em:")
    print(f"   {OUTPUT_DIR}")
    print()
    print("=" * 70)
    print()
    print("Servidor rodando em http://localhost:5000")
    print()

    app.run(host='0.0.0.0', port=5000, debug=True)
