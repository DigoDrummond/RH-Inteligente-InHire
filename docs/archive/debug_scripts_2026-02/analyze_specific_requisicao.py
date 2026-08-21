"""
Analisar a requisição específica sugerida pelo usuário
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
        print("ANÁLISE DA REQUISIÇÃO: 1f40bc32-90ef-416e-9c0b-846e81154da2")
        print("=" * 100)

        # ID sugerido pelo usuário
        req_inhire_id = '1f40bc32-90ef-416e-9c0b-846e81154da2'
        vaga_id_esperado = 1196
        posicao_id_esperada = 1559

        # 1. Buscar a requisição
        print("\n1. DADOS DA REQUISIÇÃO")
        print("-" * 100)
        cursor.execute("""
            SELECT id, inhire_id, name, vaga_id, job_inhire_id, status,
                   positions, custom_fields, created_at
            FROM requisicoes
            WHERE inhire_id = %s
        """, (req_inhire_id,))

        req = cursor.fetchone()
        if not req:
            print(f"[X] Requisição com inhire_id {req_inhire_id} NÃO ENCONTRADA!")
            return

        print(f"Requisição ID (BD): {req[0]}")
        print(f"Inhire ID: {req[1]}")
        print(f"Nome: {req[2]}")
        print(f"vaga_id atual: {req[3]}")
        print(f"job_inhire_id: {req[4]}")
        print(f"Status: {req[5]}")
        print(f"Criada em: {req[8]}")

        # Parse positions
        print(f"\nPositions (JSON):")
        if req[6]:
            try:
                positions = req[6] if isinstance(req[6], list) else json.loads(req[6])
                print(f"  Total de positions: {len(positions)}")
                for pos in positions:
                    print(f"  - Position ID: {pos.get('id')}")
                    print(f"    Name: {pos.get('name', 'N/A')}")
                    print(f"    Amount: {pos.get('amount', 'N/A')}")
            except Exception as e:
                print(f"  ERRO ao parsear: {e}")
        else:
            print("  NULL ou vazio")

        # Custom fields (resumido)
        print(f"\nCustom Fields (resumo):")
        if req[7]:
            try:
                cf = req[7] if isinstance(req[7], list) else json.loads(req[7])
                if isinstance(cf, list):
                    for field in cf[:5]:  # Apenas primeiros 5
                        print(f"  - {field.get('name')}: {field.get('value')}")
                    if len(cf) > 5:
                        print(f"  ... e mais {len(cf) - 5} campos")
            except:
                print("  (erro ao parsear)")
        else:
            print("  NULL ou vazio")

        # 2. Buscar a vaga esperada
        print("\n2. VAGA ESPERADA (ID 1196)")
        print("-" * 100)
        cursor.execute("""
            SELECT id, name, inhire_id, created_at
            FROM vagas
            WHERE id = %s
        """, (vaga_id_esperado,))

        vaga = cursor.fetchone()
        if vaga:
            print(f"Vaga ID: {vaga[0]}")
            print(f"Nome: {vaga[1]}")
            print(f"Inhire ID: {vaga[2]}")
            print(f"Criada em: {vaga[3]}")
        else:
            print(f"[X] Vaga {vaga_id_esperado} não encontrada!")

        # 3. Buscar a posição esperada
        print("\n3. POSIÇÃO ESPERADA (ID 1559)")
        print("-" * 100)
        cursor.execute("""
            SELECT id, vaga_id, inhire_id, created_at
            FROM posicoes
            WHERE id = %s
        """, (posicao_id_esperada,))

        pos = cursor.fetchone()
        if pos:
            print(f"Posição ID: {pos[0]}")
            print(f"Vaga ID: {pos[1]}")
            print(f"Inhire ID: {pos[2]}")
            print(f"Criada em: {pos[3]}")
        else:
            print(f"[X] Posição {posicao_id_esperada} não encontrada!")

        # 4. Análise de vínculo
        print("\n4. ANÁLISE DE VÍNCULO")
        print("-" * 100)

        if req and vaga and pos:
            # Verificar se position está no campo positions da requisição
            if req[6]:
                try:
                    positions = req[6] if isinstance(req[6], list) else json.loads(req[6])
                    position_ids = [p.get('id') for p in positions if p.get('id')]

                    if pos[2] in position_ids:  # pos[2] é inhire_id da posição
                        print(f"[OK] Position {pos[2]} ESTÁ no campo positions da requisição!")
                    else:
                        print(f"[X] Position {pos[2]} NÃO está no campo positions")
                        print(f"    Positions encontrados: {position_ids}")
                except:
                    print("[?] Não foi possível verificar positions")

            # Verificar se job_inhire_id bate com vaga.inhire_id
            if req[4] == vaga[2]:
                print(f"[OK] job_inhire_id BATE com vaga.inhire_id!")
            else:
                print(f"[X] job_inhire_id NÃO BATE:")
                print(f"    Requisição job_inhire_id: {req[4]}")
                print(f"    Vaga inhire_id: {vaga[2]}")

            # Verificar vaga_id atual
            if req[3] == vaga_id_esperado:
                print(f"[OK] vaga_id JÁ ESTÁ CORRETO!")
            elif req[3] is None:
                print(f"[AÇÃO] vaga_id está NULL. Deveria ser {vaga_id_esperado}")
            else:
                print(f"[AÇÃO] vaga_id está ERRADO. É {req[3]}, deveria ser {vaga_id_esperado}")

        # 5. Buscar todas as requisições que mencionam a posição 1559
        print("\n5. OUTRAS REQUISIÇÕES QUE MENCIONAM A POSIÇÃO 1559")
        print("-" * 100)
        cursor.execute("""
            SELECT id, inhire_id, name, vaga_id, positions
            FROM requisicoes
            WHERE positions::text LIKE %s
        """, (f'%{pos[2]}%',))

        outras = cursor.fetchall()
        print(f"Total encontrado: {len(outras)}")
        for outra in outras:
            print(f"\nRequisição {outra[0]}:")
            print(f"  Inhire ID: {outra[1]}")
            print(f"  Nome: {outra[2]}")
            print(f"  vaga_id: {outra[3]}")

        # 6. Padrão geral - verificar como outras vagas estão linkadas
        print("\n6. PADRÃO DE LINKING (amostra)")
        print("-" * 100)
        cursor.execute("""
            SELECT
                r.id, r.name, r.vaga_id, r.job_inhire_id,
                v.id as vaga_bd_id, v.inhire_id as vaga_inhire_id
            FROM requisicoes r
            INNER JOIN vagas v ON v.id = r.vaga_id
            WHERE r.vaga_id IS NOT NULL
            LIMIT 5
        """)

        print("Exemplos de requisições corretamente linkadas:")
        for row in cursor.fetchall():
            print(f"\nReq {row[0]}: {row[1][:40]}")
            print(f"  vaga_id: {row[2]}")
            print(f"  job_inhire_id: {row[3]}")
            print(f"  Vaga BD ID: {row[4]}")
            print(f"  Vaga Inhire ID: {row[5]}")
            print(f"  Match: job_inhire_id == vaga.inhire_id? {row[3] == row[5]}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 100)
        print("ANÁLISE CONCLUÍDA")
        print("=" * 100)

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
