"""
Verificar se existem requisições no banco com os positions IDs das vagas problemáticas
"""
import psycopg2
import json

def main():
    try:
        conn = psycopg2.connect(
            dbname="inhire",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        print("=" * 100)
        print("VERIFICANDO REQUISIÇÕES POR POSITION ID")
        print("=" * 100)

        # Vagas e suas posições (do output anterior)
        vagas_posicoes = {
            1193: ('31e7ad35-81c1-4597-b1da-ef01a1fb5154', '01f3d82d-63ce-46ae-a386-1286c4a0f7cd', 'Product Manager Pleno'),
            1196: ('152500e7-cadf-458c-b851-baff1d91f94a', '4f99a7fd-4533-4f2b-9971-4caff86b3f8f', 'Desenvolvedor .NET Sênior'),
            1205: ('47187249-c21d-4d85-9be5-b6700b7c32d3', '59527d2d-439c-49d9-8d1e-33d2514c5cab', 'Desenvolvedor Fullstack Pleno'),
            1207: ('340b053b-f862-48cc-aa1f-b68dea20edba', 'e63c9127-5d61-4672-82e0-481329d8656b', 'a252 Desenvolvedor .NET Sênior'),
            1212: ('7c7864b3-d2c1-472a-b2f0-8bf48eab658f', '83017f21-5993-4697-8771-b021acbc010c', 'IT Business Partner'),
            1211: ('6ff7ed35-4690-43d8-9563-f9d8a5e37e82', '39f8a933-6329-4b96-8954-78f0324c7d40', 'Analista de CRM Sênior')
        }

        print("\n1. BUSCANDO REQUISIÇÕES POR POSITION ID (no campo JSON 'positions')")
        print("-" * 100)

        for vaga_id, (position_id, job_id, vaga_nome) in vagas_posicoes.items():
            print(f"\n--- Vaga {vaga_id}: {vaga_nome} ---")
            print(f"Position ID: {position_id}")
            print(f"Job ID: {job_id}")

            # Método 1: Buscar por positions JSON contendo o position_id
            cursor.execute("""
                SELECT id, inhire_id, name, vaga_id, job_inhire_id, status, positions
                FROM requisicoes
                WHERE positions::text LIKE %s
            """, (f'%{position_id}%',))

            results = cursor.fetchall()

            if results:
                print(f"  [OK] Encontrado {len(results)} requisição(ões) com este position_id:")
                for row in results:
                    req_id, req_inhire_id, req_name, req_vaga_id, req_job_id, req_status, positions_json = row
                    print(f"\n  Requisição ID: {req_id}")
                    print(f"    Inhire ID: {req_inhire_id}")
                    print(f"    Nome: {req_name}")
                    print(f"    Vaga ID vinculado: {req_vaga_id}")
                    print(f"    Job Inhire ID: {req_job_id}")
                    print(f"    Status: {req_status}")

                    # Parse positions JSON
                    if positions_json:
                        try:
                            positions = positions_json if isinstance(positions_json, list) else json.loads(positions_json)
                            position_ids = [p.get('id') for p in positions if p.get('id')]
                            print(f"    Positions IDs: {position_ids}")
                        except:
                            print(f"    Positions: (erro ao parsear)")

                    # Verificar se está linkado corretamente
                    if req_vaga_id == vaga_id:
                        print(f"    [OK] JÁ VINCULADO CORRETAMENTE!")
                    elif req_vaga_id is None:
                        print(f"    [PROBLEMA] vaga_id está NULL! Precisa linkar com vaga {vaga_id}")
                    else:
                        print(f"    [PROBLEMA] Vinculado com vaga errada ({req_vaga_id}). Deveria ser {vaga_id}")

            else:
                print(f"  [X] NENHUMA requisição encontrada com este position_id")

                # Tentar buscar por job_inhire_id
                cursor.execute("""
                    SELECT id, inhire_id, name, vaga_id, job_inhire_id
                    FROM requisicoes
                    WHERE job_inhire_id = %s
                """, (job_id,))

                job_results = cursor.fetchall()
                if job_results:
                    print(f"\n  [INFO] Encontrado requisição por job_inhire_id:")
                    for row in job_results:
                        print(f"    Requisição ID: {row[0]}, vaga_id: {row[3]}")
                else:
                    print(f"  [X] Também não encontrado por job_inhire_id")

        print("\n2. RESUMO GERAL")
        print("-" * 100)

        total_vagas = len(vagas_posicoes)
        vagas_com_req = 0
        vagas_req_null = 0
        vagas_req_errado = 0

        for vaga_id, (position_id, _, _) in vagas_posicoes.items():
            cursor.execute("""
                SELECT vaga_id FROM requisicoes WHERE positions::text LIKE %s
            """, (f'%{position_id}%',))
            result = cursor.fetchone()

            if result:
                if result[0] == vaga_id:
                    vagas_com_req += 1
                elif result[0] is None:
                    vagas_req_null += 1
                else:
                    vagas_req_errado += 1

        print(f"Total de vagas analisadas:                {total_vagas}")
        print(f"Com requisição corretamente vinculada:    {vagas_com_req}")
        print(f"Com requisição mas vaga_id NULL:          {vagas_req_null}")
        print(f"Com requisição mas vaga_id errado:        {vagas_req_errado}")
        print(f"Sem requisição encontrada:                {total_vagas - vagas_com_req - vagas_req_null - vagas_req_errado}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 100)
        print("VERIFICAÇÃO CONCLUÍDA")
        print("=" * 100)

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
