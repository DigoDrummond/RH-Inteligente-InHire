# -*- coding: utf-8 -*-
"""
Script para validar custom fields do ADLER via API (usando AuthService)
NÃO executa sincronização - apenas consulta e testa conversão
"""
import sys
import os
import json
from dotenv import load_dotenv

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar .env
load_dotenv()

# Importar serviços
from services.auth_service import AuthService
from services.api_client import InhireAPIClient

print("\n" + "="*80)
print("VALIDAÇÃO DE CUSTOM FIELDS - CANDIDATO ADLER")
print("="*80)

ADLER_EMAIL = 'adlerbcc95@hotmail.com'
CUSTOM_FIELD_ID = '55282edb-bb11-4445-8cd6-3c0c6b9ddb9a'

print(f"\n1. Autenticando na API...")
try:
    auth_service = AuthService()
    if not auth_service.authenticate():
        raise Exception("Falha na autenticação")

    api_client = InhireAPIClient(auth_service=auth_service)
    print("   ✅ Autenticado com sucesso!")
except Exception as e:
    print(f"   ❌ Erro na autenticação: {e}")
    sys.exit(1)

print(f"\n2. Buscando candidaturas do ADLER (email: {ADLER_EMAIL})...")

# Buscar talentos com nome/email ADLER
print(f"\n   a) Buscando talento por email/nome...")

candidaturas_encontradas = []

try:
    # Buscar via paginação de talentos
    talentos = list(api_client.listar_talentos_paginados(limit=200))
    print(f"      - Buscados {len(talentos)} talentos")

    adler_talent = None
    for talent in talentos:
        email = getattr(talent, 'email', None) or ''
        name = getattr(talent, 'name', None) or ''

        if (email.lower() == ADLER_EMAIL.lower() or
            'adler' in name.lower()):
            adler_talent = talent
            break

    if not adler_talent:
        print(f"   ❌ Talento ADLER não encontrado!")
        sys.exit(1)

    print(f"   ✅ Talento encontrado:")
    print(f"      - ID: {adler_talent.id}")
    print(f"      - Nome: {adler_talent.name}")
    print(f"      - Email: {adler_talent.email}")

    talent_id = adler_talent.id

except Exception as e:
    print(f"   ❌ Erro ao buscar talento: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Buscar candidaturas do ADLER
print(f"\n   b) Buscando candidaturas do talento...")

try:
    # Buscar vagas para encontrar candidaturas
    vagas = list(api_client.get_all_vagas())
    print(f"      - Encontradas {len(vagas)} vagas no total")

    # Limitar busca a 20 vagas mais recentes para não demorar
    vagas_recentes = sorted(
        vagas,
        key=lambda v: getattr(v, 'updatedAt', '') or '',
        reverse=True
    )[:20]

    print(f"      - Buscando em 20 vagas mais recentes...")

    for i, vaga in enumerate(vagas_recentes, 1):
        try:
            # Buscar candidaturas desta vaga
            cands = api_client.listar_candidaturas_paginadas(vaga.id, limit=100)

            if not cands or not hasattr(cands, 'jobTalents'):
                continue

            # Procurar ADLER
            for cand in cands.jobTalents:
                if cand.talentId == talent_id:
                    candidaturas_encontradas.append({
                        'vaga': vaga,
                        'candidatura': cand
                    })
                    print(f"      ✅ Candidatura encontrada na vaga '{vaga.name}'!")

            if candidaturas_encontradas:
                break

        except Exception as e:
            continue

    if not candidaturas_encontradas:
        print(f"   ⚠️ Nenhuma candidatura encontrada nas 20 vagas mais recentes")

except Exception as e:
    print(f"   ❌ Erro ao buscar candidaturas: {e}")
    import traceback
    traceback.print_exc()

if candidaturas_encontradas:
    print(f"\n3. Analisando customFields da primeira candidatura encontrada...")

    primeira_cand = candidaturas_encontradas[0]['candidatura']
    vaga = candidaturas_encontradas[0]['vaga']

    print(f"\n   📋 Dados da candidatura:")
    print(f"      - ID: {primeira_cand.id}")
    print(f"      - Vaga: {vaga.name}")
    print(f"      - Status: {primeira_cand.status}")

    custom_fields_raw = primeira_cand.customFields

    print(f"\n   📦 customFields BRUTO retornado pela API:")
    print(f"      - Tipo: {type(custom_fields_raw)}")
    print(f"      - Valor:")

    # Converter para dict para exibir
    if hasattr(custom_fields_raw, '__dict__'):
        print(json.dumps(custom_fields_raw.__dict__, indent=8, ensure_ascii=False, default=str))
    else:
        print(json.dumps(custom_fields_raw, indent=8, ensure_ascii=False, default=str))

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

    if converted is None:
        print(f"      - Valor: None (sem custom fields ou formato não reconhecido)")
    else:
        print(f"      - Valor:")
        print(json.dumps(converted, indent=8, ensure_ascii=False, default=str))

        # Verificar campo específico
        print(f"\n5. Verificando campo 'Você conhecia a Framework Digital?'...")
        print(f"   ID do campo: {CUSTOM_FIELD_ID}")

        if CUSTOM_FIELD_ID in converted:
            valor = converted[CUSTOM_FIELD_ID]
            print(f"\n   ✅ Campo encontrado!")
            print(f"      - Tipo: {type(valor)}")
            print(f"      - Valor completo: {valor}")

            if isinstance(valor, list) and len(valor) > 0:
                print(f"      - Primeira resposta: {valor[0]}")
                print(f"\n   🎯 RESPOSTA FINAL QUE SERÁ SALVA NO BD: '{valor[0]}'")
            else:
                print(f"      ⚠️ Valor não é uma lista ou está vazio")
        else:
            print(f"\n   ❌ Campo NÃO encontrado no dicionário convertido!")
            print(f"      Campos disponíveis: {list(converted.keys())}")

else:
    print(f"\n❌ Nenhuma candidatura do ADLER encontrada para validar")
    print(f"   O talento foi encontrado, mas não tem candidaturas recentes")

print(f"\n" + "="*80)
print("VALIDAÇÃO CONCLUÍDA!")
print("="*80 + "\n")
