"""
Teste direto da API para buscar requisições das vagas problem áticas
Versão simplificada sem dependências de módulos internos
"""
import psycopg2
import requests
import os
from dotenv import load_dotenv
import json

# Carregar variáveis de ambiente
load_dotenv()

def authenticate():
    """Autenticar na API do InHire"""
    auth_url = "https://auth.inhire.app/auth/login"
    payload = {
        "email": os.getenv("INHIRE_EMAIL"),
        "password": os.getenv("INHIRE_PASSWORD"),
        "tenantId": os.getenv("INHIRE_TENANT")
    }

    print("Autenticando na API...")
    response = requests.post(auth_url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("accessToken")

def get_requisitions(token):
    """Buscar todas as requisições da API"""
    api_url = "https://api.inhire.app/api/requisitions/list"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-tenant-id": os.getenv("INHIRE_TENANT")
    }

    all_requisitions = []
    page = 1
    page_size = 100

    print("Buscando requisições da API...")
    while True:
        payload = {
            "page": page,
            "pageSize": page_size
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        requisitions = data.get("requisitions", [])
        if not requisitions:
            break

        all_requisitions.extend(requisitions)
        print(f"  Página {page}: {len(requisitions)} requisições ({len(all_requisitions)} total)")
        page += 1

        if len(requisitions) < page_size:
            break

    return all_requisitions

def main():
    try:
        # Conectar ao banco
        conn = psycopg2.connect(
            dbname="inhire",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        print("=" * 100)
        print("TESTE DA API: REQUISIÇÕES DAS VAGAS PROBLEMÁTICAS")
        print("=" * 100)

        # Vagas problemáticas
        vagas_problema = [1193, 1196, 1205, 1207, 1212, 1211]

        print("\n1. BUSCANDO INFORMAÇÕES DAS VAGAS NO BANCO")
        print("-" * 100)

        vagas_info = {}
        for vaga_id in vagas_problema:
            cursor.execute("""
                SELECT v.id, v.name, v.inhire_id as vaga_inhire_id,
                       p.id as posicao_id, p.inhire_id as posicao_inhire_id
                FROM vagas v
                LEFT JOIN posicoes p ON p.vaga_id = v.id
                WHERE v.id = %s
            """, (vaga_id,))
            rows = cursor.fetchall()
            if rows:
                vaga_info = {
                    'id': rows[0][0],
                    'name': rows[0][1],
                    'vaga_inhire_id': rows[0][2],
                    'posicoes': [(row[3], row[4]) for row in rows if row[3]]
                }
                vagas_info[vaga_id] = vaga_info
                print(f"\nVaga {vaga_id}: {vaga_info['name']}")
                print(f"  Vaga Inhire ID: {vaga_info['vaga_inhire_id']}")
                print(f"  Posições vinculadas: {len(vaga_info['posicoes'])}")
                for pos_id, pos_inhire_id in vaga_info['posicoes']:
                    print(f"    - Posição {pos_id}: {pos_inhire_id}")

        print("\n2. AUTENTICANDO E BUSCANDO REQUISIÇÕES DA API")
        print("-" * 100)

        # Autenticar
        token = authenticate()
        print("[OK] Autenticação realizada com sucesso")

        # Buscar requisições
        all_requisitions = get_requisitions(token)
        print(f"\n[OK] Total de requisições na API: {len(all_requisitions)}")

        print("\n3. TENTANDO FAZER MATCH COM AS VAGAS")
        print("-" * 100)

        for vaga_id, vaga_info in vagas_info.items():
            print(f"\n--- Vaga {vaga_id}: {vaga_info['name']} ---")
            print(f"Vaga Inhire ID: {vaga_info['vaga_inhire_id']}")

            # Tentar match por diferentes campos
            matches_found = []

            # 1. Tentar match por positions[].id (posicao_inhire_id)
            posicao_ids = [pos[1] for pos in vaga_info['posicoes']]
            for req in all_requisitions:
                positions = req.get('positions', [])
                if not positions:
                    continue
                req_position_ids = [p.get('id') for p in positions if p.get('id')]
                if any(pos_id in req_position_ids for pos_id in posicao_ids):
                    matches_found.append(('POSITION_ID', req))

            # 2. Tentar match por jobId
            for req in all_requisitions:
                if req.get('jobId') == vaga_info['vaga_inhire_id']:
                    if not any(m[1].get('id') == req.get('id') for m in matches_found):
                        matches_found.append(('JOB_ID', req))

            # 3. Tentar match por nome (case insensitive)
            vaga_name_lower = vaga_info['name'].lower()
            for req in all_requisitions:
                if req.get('name') and req.get('name').lower() == vaga_name_lower:
                    if not any(m[1].get('id') == req.get('id') for m in matches_found):
                        matches_found.append(('NAME', req))

            # Resultados
            if matches_found:
                print(f"  [OK] Encontrado {len(matches_found)} match(es):")
                for match_type, req in matches_found:
                    print(f"\n  Match por {match_type}:")
                    print(f"    Requisição ID (DB): {req.get('id')}")
                    print(f"    Requisição Inhire ID: {req.get('inhireId')}")
                    print(f"    Nome: {req.get('name')}")
                    print(f"    Job ID: {req.get('jobId')}")
                    print(f"    Status: {req.get('status')}")
                    positions = req.get('positions', [])
                    if positions:
                        print(f"    Positions IDs: {[p.get('id') for p in positions]}")

                    # Verificar se existe no banco
                    cursor.execute("""
                        SELECT id, vaga_id, job_inhire_id
                        FROM requisicoes
                        WHERE inhire_id = %s
                    """, (req.get('inhireId'),))
                    db_req = cursor.fetchone()
                    if db_req:
                        print(f"    [INFO] JÁ EXISTE NO BANCO:")
                        print(f"      Requisição BD ID: {db_req[0]}")
                        print(f"      Vaga ID vinculado: {db_req[1]}")
                        print(f"      Job Inhire ID: {db_req[2]}")
                        if db_req[1] != vaga_id:
                            print(f"      [PROBLEMA] Vaga vinculada errada! Esperado {vaga_id}, encontrado {db_req[1]}")
                        if db_req[1] is None:
                            print(f"      [PROBLEMA] vaga_id está NULL!")
                    else:
                        print(f"    [PROBLEMA] NÃO EXISTE NO BANCO!")
            else:
                print(f"  [X] NENHUM MATCH ENCONTRADO!")
                print(f"  Sugestão: verificar manualmente no InHire se a requisição existe")

        print("\n4. ESTATÍSTICAS DE REQUISIÇÕES NA API vs BANCO")
        print("-" * 100)
        cursor.execute("SELECT COUNT(*) FROM requisicoes")
        total_bd = cursor.fetchone()[0]
        print(f"  Total na API:   {len(all_requisitions)}")
        print(f"  Total no Banco: {total_bd}")
        print(f"  Diferença:      {len(all_requisitions) - total_bd}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 100)
        print("TESTE CONCLUÍDO")
        print("=" * 100)

    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
