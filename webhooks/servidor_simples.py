"""
Servidor Webhook Simples - Versao de Teste
Sem emojis, sem problemas de encoding
"""

from flask import Flask, request, jsonify
import csv
import os
from datetime import datetime

# TOKEN FIXO PARA TESTES
SECRET_TOKEN = "meu-token-secreto-123"

# Diretorio de saida
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "webhooks_recebidos")
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)


def processar_candidatura(payload):
    """Processa candidatura"""
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


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "service": "Webhook Receiver",
        "status": "running",
        "token": SECRET_TOKEN
    })


@app.route('/job-talent-added', methods=['POST'])
def webhook_candidatura():
    try:
        # Validar token
        auth_header = request.headers.get('Authorization')
        expected = f"Bearer {SECRET_TOKEN}"

        if auth_header != expected:
            print(f"[ERRO] Token invalido")
            print(f"  Recebido: {auth_header}")
            print(f"  Esperado: {expected}")
            return jsonify({"error": "Unauthorized"}), 401

        # Processar payload
        payload = request.get_json()

        print("\n" + "=" * 70)
        print(f"[WEBHOOK] Candidatura recebida")
        print("=" * 70)
        print(f"Vaga: {payload.get('jobName')}")
        print(f"Candidato: {payload.get('talentId')}")
        print(f"Etapa: {payload.get('stageName')}")

        resultado = processar_candidatura(payload)

        print(f"[OK] {resultado['message']}")
        print("=" * 70)
        print()

        return jsonify({
            "status": "success",
            "message": resultado['message']
        })

    except Exception as e:
        print(f"[ERRO] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("SERVIDOR WEBHOOK - TESTE SIMPLES")
    print("=" * 70)
    print(f"\nToken: {SECRET_TOKEN}")
    print(f"Header: Authorization: Bearer {SECRET_TOKEN}")
    print("\nServidor rodando em http://localhost:5000")
    print("=" * 70 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=False)
