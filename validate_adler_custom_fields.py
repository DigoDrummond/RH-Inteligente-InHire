# -*- coding: utf-8 -*-
"""
Script para validar custom fields do ADLER via API
NÃO executa sincronização - apenas consulta e testa conversão
"""
import sys
import os
import json
import requests
from dotenv import load_dotenv

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar .env
load_dotenv()

print("\n" + "="*80)
print("VALIDAÇÃO DE CUSTOM FIELDS - CANDIDATO ADLER")
print("="*80)

# Configurações
API_URL = os.getenv('INHIRE_API_URL', 'https://api.inhire.app').rstrip('/')
AUTH_URL = os.getenv('INHIRE_AUTH_URL', 'https://auth.inhire.app').rstrip('/')
EMAIL = os.getenv('INHIRE_EMAIL')
PASSWORD = os.getenv('INHIRE_PASSWORD')
ADLER_EMAIL = 'adlerbcc95@hotmail.com'
CUSTOM_FIELD_ID = '55282edb-bb11-4445-8cd6-3c0c6b9ddb9a'

print(f"\n1. Autenticando na API...")
try:
    auth_response = requests.post(
        f"{AUTH_URL}/users/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30
    )
    auth_response.raise_for_status()
    auth_data = auth_response.json()
    access_token = auth_data['accessToken']
    print("   ✅ Autenticado com sucesso!")
except Exception as e:
    print(f"   ❌ Erro na autenticação: {e}")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

print(f"\n2. Buscando candidaturas do ADLER (email: {ADLER_EMAIL})...")

# Primeiro, vamos buscar o talento ADLER
print(f"\n   a) Buscando talento por email...")
try:
    # Buscar via endpoint de talentos paginados
    talents_response = requests.post(
        f"{API_URL}/talents/paginated",
        headers=headers,
        json={
            "limit": 50,
            "filter": {
                "email": {"$regex": "adler", "$options": "i"}
            }
        },
        timeout=30
    )
    talents_response.raise_for_status()
    talents_data = talents_response.json()

    adler_talent = None
    for talent in talents_data.get('items', []):
        if talent.get('email', '').lower() == ADLER_EMAIL.lower():
            adler_talent = talent
            break

    if not adler_talent:
        print(f"   ⚠️ Talento ADLER não encontrado via email")
        print(f"   Tentando buscar por nome...")

        talents_response = requests.post(
            f"{API_URL}/talents/paginated",
            headers=headers,
            json={
                "limit": 50,
                "filter": {
                    "name": {"$regex": "adler", "$options": "i"}
                }
            },
            timeout=30
        )
        talents_response.raise_for_status()
        talents_data = talents_response.json()

        if talents_data.get('items'):
            adler_talent = talents_data['items'][0]

    if not adler_talent:
        print(f"   ❌ Talento ADLER não encontrado!")
        sys.exit(1)

    print(f"   ✅ Talento encontrado:")
    print(f"      - ID: {adler_talent.get('id')}")
    print(f"      - Nome: {adler_talent.get('name')}")
    print(f"      - Email: {adler_talent.get('email')}")

except Exception as e:
    print(f"   ❌ Erro ao buscar talento: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Agora buscar candidaturas deste talento
print(f"\n   b) Buscando candidaturas do talento...")

talent_id = adler_talent['id']
candidaturas_encontradas = []

try:
    # Buscar todas as vagas e depois filtrar candidaturas do ADLER
    # (A API não tem endpoint direto para buscar candidaturas por talentId)

    # Vamos pegar as candidaturas de cada vaga
    print(f"      Buscando vagas para encontrar candidaturas...")

    vagas_response = requests.post(
        f"{API_URL}/jobs/paginated/lean",
        headers=headers,
        json={"limit": 100},
        timeout=30
    )
    vagas_response.raise_for_status()
    vagas_data = vagas_response.json()

    vagas_ids = [v['id'] for v in vagas_data.get('results', [])]
    print(f"      - Encontradas {len(vagas_ids)} vagas")

    # Buscar candidaturas em cada vaga (limitando a 10 vagas para teste)
    for i, vaga_id in enumerate(vagas_ids[:10], 1):
        try:
            cand_response = requests.post(
                f"{API_URL}/jobs/{vaga_id}/talents/paginated",
                headers=headers,
                json={"limit": 50},
                timeout=30
            )
            cand_response.raise_for_status()
            cand_data = cand_response.json()

            # Filtrar candidaturas do ADLER
            for cand in cand_data.get('jobTalents', []):
                if cand.get('talentId') == talent_id:
                    candidaturas_encontradas.append({
                        'vaga_id': vaga_id,
                        'candidatura': cand
                    })
                    print(f"      ✅ Candidatura encontrada na vaga {i}/10!")

            if candidaturas_encontradas:
                break

        except Exception as e:
            continue

    if not candidaturas_encontradas:
        print(f"   ⚠️ Nenhuma candidatura encontrada nas primeiras 10 vagas")
        print(f"   (Limitamos a busca para não demorar muito)")

except Exception as e:
    print(f"   ❌ Erro ao buscar candidaturas: {e}")
    import traceback
    traceback.print_exc()

if candidaturas_encontradas:
    print(f"\n3. Analisando customFields da primeira candidatura encontrada...")

    primeira_cand = candidaturas_encontradas[0]['candidatura']

    print(f"\n   📋 Dados da candidatura:")
    print(f"      - ID: {primeira_cand.get('id')}")
    print(f"      - Vaga ID: {candidaturas_encontradas[0]['vaga_id']}")
    print(f"      - Status: {primeira_cand.get('status')}")

    custom_fields_raw = primeira_cand.get('customFields')

    print(f"\n   📦 customFields BRUTO retornado pela API:")
    print(f"      - Tipo: {type(custom_fields_raw)}")
    print(f"      - Valor:")
    print(json.dumps(custom_fields_raw, indent=8, ensure_ascii=False))

    # Testar conversão
    print(f"\n4. Testando conversão de customFields...")

    def convert_custom_fields_to_dict(custom_fields):
        """Função de conversão (mesma do database_service.py)"""
        if not custom_fields:
            return None

        # Se já é um dicionário, retornar como está
        if isinstance(custom_fields, dict):
            return custom_fields

        # Se é uma lista, converter para dicionário
        if isinstance(custom_fields, list):
            result = {}
            for field in custom_fields:
                if isinstance(field, dict):
                    field_id = field.get('id') or field.get('name')
                    field_value = field.get('value', [])

                    # Garantir que value é uma lista
                    if not isinstance(field_value, list):
                        field_value = [field_value] if field_value else []

                    if field_id:
                        result[field_id] = field_value

            return result if result else None

        # Formato desconhecido
        return None

    converted = convert_custom_fields_to_dict(custom_fields_raw)

    print(f"\n   ✅ RESULTADO da conversão:")
    print(f"      - Tipo: {type(converted)}")
    print(f"      - Valor:")
    print(json.dumps(converted, indent=8, ensure_ascii=False))

    # Verificar campo específico
    print(f"\n5. Verificando campo 'Você conhecia a Framework Digital?'...")
    print(f"   ID do campo: {CUSTOM_FIELD_ID}")

    if converted and CUSTOM_FIELD_ID in converted:
        valor = converted[CUSTOM_FIELD_ID]
        print(f"\n   ✅ Campo encontrado!")
        print(f"      - Tipo: {type(valor)}")
        print(f"      - Valor completo: {valor}")

        if isinstance(valor, list) and len(valor) > 0:
            print(f"      - Primeira resposta: {valor[0]}")
            print(f"\n   🎯 RESPOSTA FINAL: {valor[0]}")
        else:
            print(f"      ⚠️ Valor não é uma lista ou está vazio")
    else:
        print(f"\n   ❌ Campo NÃO encontrado no dicionário convertido!")
        if converted:
            print(f"      Campos disponíveis: {list(converted.keys())}")

else:
    print(f"\n❌ Nenhuma candidatura do ADLER encontrada para validar")

print(f"\n" + "="*80)
print("VALIDAÇÃO CONCLUÍDA!")
print("="*80 + "\n")
