"""
Analisar a extensão do problema de requisições com campos NULL
"""
import psycopg2

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
        print("ANÁLISE DA EXTENSÃO DO PROBLEMA - REQUISIÇÕES")
        print("=" * 100)

        # Total de requisições
        cursor.execute("SELECT COUNT(*) FROM requisicoes")
        total = cursor.fetchone()[0]
        print(f"\nTotal de requisições: {total}")

        # job_inhire_id NULL
        cursor.execute("SELECT COUNT(*) FROM requisicoes WHERE job_inhire_id IS NULL")
        job_null = cursor.fetchone()[0]
        print(f"\nRequisições com job_inhire_id NULL: {job_null} ({job_null/total*100:.1f}%)")

        # vaga_id NULL
        cursor.execute("SELECT COUNT(*) FROM requisicoes WHERE vaga_id IS NULL")
        vaga_null = cursor.fetchone()[0]
        print(f"Requisições com vaga_id NULL: {vaga_null} ({vaga_null/total*100:.1f}%)")

        # AMBOS NULL (pior caso)
        cursor.execute("SELECT COUNT(*) FROM requisicoes WHERE job_inhire_id IS NULL AND vaga_id IS NULL")
        both_null = cursor.fetchone()[0]
        print(f"Requisições com AMBOS NULL: {both_null} ({both_null/total*100:.1f}%)")
        print(f"  >> Estas requisições NAO PODEM ser linkadas automaticamente!")

        # Apenas job_inhire_id NULL mas vaga_id preenchido (pode ser resolvido)
        cursor.execute("SELECT COUNT(*) FROM requisicoes WHERE job_inhire_id IS NULL AND vaga_id IS NOT NULL")
        recoverable = cursor.fetchone()[0]
        print(f"\nRequisições com job_inhire_id NULL mas vaga_id OK: {recoverable}")
        print(f"  >> Estas ja estao linkadas corretamente!")

        # name NULL
        cursor.execute("SELECT COUNT(*) FROM requisicoes WHERE name IS NULL")
        name_null = cursor.fetchone()[0]
        print(f"\nRequisições com name NULL: {name_null} ({name_null/total*100:.1f}%)")

        # positions NULL
        cursor.execute("SELECT COUNT(*) FROM requisicoes WHERE positions IS NULL")
        positions_null = cursor.fetchone()[0]
        print(f"Requisições com positions NULL: {positions_null} ({positions_null/total*100:.1f}%)")

        # Verificar as 6 vagas específicas
        print("\n" + "=" * 100)
        print("ANÁLISE DAS 6 VAGAS PROBLEMÁTICAS")
        print("=" * 100)

        vagas_problema = [1193, 1196, 1205, 1207, 1212, 1211]

        for vaga_id in vagas_problema:
            cursor.execute("""
                SELECT v.id, v.name, v.inhire_id, p.inhire_id
                FROM vagas v
                LEFT JOIN posicoes p ON p.vaga_id = v.id
                WHERE v.id = %s
            """, (vaga_id,))
            row = cursor.fetchone()

            if row:
                vaga_name = row[1]
                vaga_inhire_id = row[2]
                position_inhire_id = row[3]

                # Tentar encontrar requisição por job_inhire_id
                cursor.execute("""
                    SELECT id, inhire_id, job_inhire_id, vaga_id, name
                    FROM requisicoes
                    WHERE job_inhire_id = %s
                """, (vaga_inhire_id,))
                by_job = cursor.fetchone()

                # Tentar por position no JSON
                if position_inhire_id:
                    cursor.execute("""
                        SELECT id, inhire_id, job_inhire_id, vaga_id, name
                        FROM requisicoes
                        WHERE positions::text LIKE %s
                    """, (f'%{position_inhire_id}%',))
                    by_position = cursor.fetchone()
                else:
                    by_position = None

                print(f"\nVaga {vaga_id}: {vaga_name}")
                print(f"  Vaga inhire_id: {vaga_inhire_id}")
                print(f"  Position inhire_id: {position_inhire_id}")

                if by_job:
                    print(f"  [ENCONTRADO] Requisição por job_inhire_id:")
                    print(f"    Req ID: {by_job[0]}, vaga_id: {by_job[3]}, name: {by_job[4]}")
                    if by_job[3] != vaga_id:
                        print(f"    [PROBLEMA] vaga_id incorreto! Esperado {vaga_id}, encontrado {by_job[3]}")
                elif by_position:
                    print(f"  [ENCONTRADO] Requisição por position ID:")
                    print(f"    Req ID: {by_position[0]}, job_inhire_id: {by_position[2]}, vaga_id: {by_position[3]}")
                    print(f"    [PROBLEMA] job_inhire_id NULL!")
                else:
                    print(f"  [NÃO ENCONTRADO] Nenhuma requisição encontrada!")

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
