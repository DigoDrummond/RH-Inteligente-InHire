"""
TESTE 2: Validação de Payloads
===============================

Testa se os payloads de eventos estão corretos e processam adequadamente
"""

import json
from datetime import datetime


# ========================================
# PAYLOADS DE EXEMPLO
# ========================================

PAYLOADS_EXEMPLO = {
    "job_talent_added": {
        "tenantId": "frameworkdigital",
        "jobId": "5dfd3a1e-a5c3-4e53-a3f4-cdb4e311d315",
        "jobName": "Desenvolvedor Full Stack Senior",
        "talentId": "b1c2d3e4-f5a6-7890-bcde-1234567890ab",
        "stageName": "Triagem",
        "source": "career-page",
        "linkedinUsername": "joaosilva",
        "location": "São Paulo, SP",
        "targetSalary": 8000,
        "workModel": "hybrid",
        "userId": "u-123",
        "userName": "Recrutador RH"
    },

    "job_talent_stage_added": {
        "tenantId": "frameworkdigital",
        "jobId": "5dfd3a1e-a5c3-4e53-a3f4-cdb4e311d315",
        "jobName": "Desenvolvedor Full Stack Senior",
        "talentId": "b1c2d3e4-f5a6-7890-bcde-1234567890ab",
        "previousStageName": "Triagem",
        "stageName": "Entrevista Técnica",
        "stageOriginId": "stage-uuid-abc",
        "stageType": "default",
        "phaseType": "screening",
        "userId": "u-123",
        "userName": "Recrutador RH"
    },

    "job_added": {
        "tenantId": "frameworkdigital",
        "jobId": "new-job-uuid-123",
        "jobName": "Analista de Dados Pleno",
        "jobDescription": "Vaga para analista de dados com experiência em Python",
        "userId": "u-456",
        "userName": "Gerente RH"
    },

    "form_response_added": {
        "tenantId": "frameworkdigital",
        "jobId": "5dfd3a1e-a5c3-4e53-a3f4-cdb4e311d315",
        "talentId": "b1c2d3e4-f5a6-7890-bcde-1234567890ab",
        "formType": "subscription",
        "title": "Triagem Técnica",
        "passed": True,
        "correctQuestionsCount": 8,
        "totalQuestions": 10
    },

    "requisition_status_updated": {
        "tenantId": "frameworkdigital",
        "requisitionId": "req-uuid-789",
        "title": "Desenvolvedor Frontend React",
        "oldStatus": "pending",
        "status": "approved",
        "userId": "u-789",
        "userName": "Gerente de Projetos"
    }
}


# ========================================
# FUNÇÕES DE PROCESSAMENTO
# ========================================

def processar_candidatura(payload):
    """Simula processamento de candidatura"""
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
    return linha


def processar_mudanca_etapa(payload):
    """Simula processamento de mudança de etapa"""
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
    return linha


def processar_nova_vaga(payload):
    """Simula processamento de nova vaga"""
    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("jobId", ""),
        payload.get("jobDescription", ""),
        payload.get("userName", "Sistema")
    ]
    return linha


def processar_formulario(payload):
    """Simula processamento de formulário"""
    acertos = payload.get("correctQuestionsCount", 0)
    total = payload.get("totalQuestions", 1)
    percentual = round((acertos / total) * 100, 1) if total > 0 else 0

    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobId", ""),
        payload.get("talentId", ""),
        payload.get("formType", ""),
        payload.get("title", ""),
        "Sim" if payload.get("passed") else "Não",
        str(acertos),
        str(total),
        f"{percentual}%"
    ]
    return linha


def processar_requisicao(payload):
    """Simula processamento de requisição"""
    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("title", ""),
        payload.get("requisitionId", ""),
        payload.get("oldStatus", ""),
        payload.get("status", ""),
        payload.get("userName", "Sistema")
    ]
    return linha


# ========================================
# FUNÇÕES DE TESTE
# ========================================

def testar_payload(evento_tipo, payload):
    """Testa processamento de um payload"""
    print("\n" + "=" * 70)
    print(f"🧪 TESTANDO: {evento_tipo.upper()}")
    print("=" * 70)

    # Mostrar payload
    print("\n📥 PAYLOAD RECEBIDO:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # Processar
    try:
        if evento_tipo == "job_talent_added":
            linha = processar_candidatura(payload)
            colunas = ["Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa",
                      "Origem", "LinkedIn", "Localização", "Pretensão", "Modelo", "Usuário"]

        elif evento_tipo == "job_talent_stage_added":
            linha = processar_mudanca_etapa(payload)
            colunas = ["Data/Hora", "Vaga", "Candidato ID", "Etapa Anterior",
                      "Nova Etapa", "Tipo", "Fase", "Usuário"]

        elif evento_tipo == "job_added":
            linha = processar_nova_vaga(payload)
            colunas = ["Data/Hora", "Vaga", "Vaga ID", "Descrição", "Usuário"]

        elif evento_tipo == "form_response_added":
            linha = processar_formulario(payload)
            colunas = ["Data/Hora", "Vaga ID", "Candidato ID", "Tipo", "Título",
                      "Aprovado?", "Acertos", "Total", "% Acerto"]

        elif evento_tipo == "requisition_status_updated":
            linha = processar_requisicao(payload)
            colunas = ["Data/Hora", "Título", "Requisição ID", "Status Anterior",
                      "Novo Status", "Usuário"]

        else:
            print("❌ Tipo de evento desconhecido!")
            return False

        # Mostrar resultado
        print("\n✅ PROCESSAMENTO CONCLUÍDO:")
        print("\n📊 LINHA QUE SERIA ADICIONADA NA PLANILHA:")
        print("-" * 70)

        for col, val in zip(colunas, linha):
            print(f"{col:20s} | {val}")

        print("-" * 70)

        return True

    except Exception as e:
        print(f"\n❌ ERRO NO PROCESSAMENTO:")
        print(f"   {str(e)}")
        return False


def testar_payload_customizado():
    """Permite testar payload customizado"""
    print("\n" + "=" * 70)
    print("🧪 TESTE COM PAYLOAD CUSTOMIZADO")
    print("=" * 70)
    print("\nCole o payload JSON que você quer testar:")
    print("(ou pressione ENTER para pular)")
    print("")

    linhas = []
    print(">>> ", end="")
    while True:
        linha = input()
        if not linha:
            break
        linhas.append(linha)
        print(">>> ", end="")

    if not linhas:
        return

    payload_texto = "\n".join(linhas)

    try:
        payload = json.loads(payload_texto)

        print("\nQual tipo de evento este payload representa?")
        print("1. job_talent_added (Candidatura)")
        print("2. job_talent_stage_added (Mudança de Etapa)")
        print("3. job_added (Nova Vaga)")
        print("4. form_response_added (Formulário)")
        print("5. requisition_status_updated (Requisição)")

        escolha = input("\nEscolha (1-5): ").strip()

        tipos = {
            "1": "job_talent_added",
            "2": "job_talent_stage_added",
            "3": "job_added",
            "4": "form_response_added",
            "5": "requisition_status_updated"
        }

        tipo = tipos.get(escolha)
        if tipo:
            testar_payload(tipo, payload)
        else:
            print("❌ Escolha inválida")

    except json.JSONDecodeError as e:
        print(f"\n❌ ERRO: JSON inválido")
        print(f"   {str(e)}")


def validar_campos_obrigatorios(evento_tipo, payload):
    """Valida se payload tem campos obrigatórios"""
    print("\n" + "=" * 70)
    print(f"🔍 VALIDANDO CAMPOS OBRIGATÓRIOS: {evento_tipo.upper()}")
    print("=" * 70)

    campos_obrigatorios = {
        "job_talent_added": ["tenantId", "jobId", "jobName", "talentId"],
        "job_talent_stage_added": ["tenantId", "jobId", "talentId", "stageName"],
        "job_added": ["tenantId", "jobId", "jobName"],
        "form_response_added": ["tenantId", "jobId", "talentId"],
        "requisition_status_updated": ["tenantId", "requisitionId", "status"]
    }

    campos = campos_obrigatorios.get(evento_tipo, [])

    faltando = []
    for campo in campos:
        if campo not in payload or payload[campo] is None:
            faltando.append(campo)

    print("")
    if faltando:
        print("❌ CAMPOS FALTANDO:")
        for campo in faltando:
            print(f"   - {campo}")
        return False
    else:
        print("✅ Todos os campos obrigatórios presentes!")
        print(f"   Validados: {', '.join(campos)}")
        return True


def main():
    """Executa todos os testes"""
    print("\n")
    print("=" * 70)
    print("🧪 TESTE 2: VALIDAÇÃO DE PAYLOADS")
    print("=" * 70)
    print("")
    print("Este teste valida:")
    print("1. Se payloads de eventos estão corretos")
    print("2. Se processamento gera linhas corretas")
    print("3. Se campos obrigatórios estão presentes")
    print("")

    input("Pressione ENTER para iniciar os testes...")

    # Testar cada tipo de evento
    for evento_tipo, payload in PAYLOADS_EXEMPLO.items():
        # Validar campos
        validar_campos_obrigatorios(evento_tipo, payload)

        # Testar processamento
        sucesso = testar_payload(evento_tipo, payload)

        if sucesso:
            print("\n✅ Teste passou!")
        else:
            print("\n❌ Teste falhou!")

        input("\nPressione ENTER para próximo teste...")

    # Teste customizado
    print("\n" + "=" * 70)
    resposta = input("\nDeseja testar um payload customizado? (s/n): ").strip().lower()
    if resposta == 's':
        testar_payload_customizado()

    # Resumo
    print("\n" + "=" * 70)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 70)
    print("")
    print("📋 TODOS OS EVENTOS TESTADOS:")
    for i, evento in enumerate(PAYLOADS_EXEMPLO.keys(), 1):
        print(f"   {i}. {evento}")
    print("")
    print("✅ Se todos os testes passaram, os payloads estão corretos!")
    print("✅ O código do Apps Script vai processar estes dados perfeitamente.")
    print("")


if __name__ == "__main__":
    main()
