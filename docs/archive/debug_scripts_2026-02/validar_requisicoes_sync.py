"""
Validar se as requisições foram sincronizadas com dados completos
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
        print("VALIDACAO: REQUISICOES APOS SYNC COM DADOS COMPLETOS")
        print("=" * 100)

        # Estatísticas gerais
        print("\n1. ESTATISTICAS GERAIS")
        print("-" * 100)
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(name) as com_nome,
                COUNT(job_inhire_id) as com_job_id,
                COUNT(vaga_id) as com_vaga_id,
                COUNT(positions) as com_positions,
                COUNT(description) as com_description
            FROM requisicoes
        """)
        row = cursor.fetchone()
        total = row[0]
        print(f"Total de requisições:        {total}")
        print(f"Com name:                    {row[1]} ({row[1]/total*100:.1f}%)")
        print(f"Com job_inhire_id:           {row[2]} ({row[2]/total*100:.1f}%)")
        print(f"Com vaga_id:                 {row[3]} ({row[3]/total*100:.1f}%)")
        print(f"Com positions:               {row[4]} ({row[4]/total*100:.1f}%)")
        print(f"Com description:             {row[5]} ({row[5]/total*100:.1f}%)")

        # Verificar a requisição 898 especificamente
        print("\n2. REQUISICAO 898 (exemplo problemático)")
        print("-" * 100)
        cursor.execute("""
            SELECT id, inhire_id, name, job_inhire_id, vaga_id,
                   CASE WHEN positions IS NOT NULL THEN 'SIM' ELSE 'NAO' END as tem_positions,
                   CASE WHEN description IS NOT NULL THEN 'SIM' ELSE 'NAO' END as tem_description
            FROM requisicoes
            WHERE inhire_id = '1f40bc32-90ef-416e-9c0b-846e81154da2'
        """)
        req = cursor.fetchone()
        if req:
            print(f"Requisição ID: {req[0]}")
            print(f"Inhire ID: {req[1]}")
            print(f"Name: {req[2] if req[2] else 'NULL'}")
            print(f"job_inhire_id: {req[3] if req[3] else 'NULL'}")
            print(f"vaga_id: {req[4] if req[4] else 'NULL'}")
            print(f"Tem positions: {req[5]}")
            print(f"Tem description: {req[6]}")
        else:
            print("[X] Requisição 898 não encontrada!")

        # Verificar as 6 vagas problemáticas
        print("\n3. VERIFICAR AS 6 VAGAS PROBLEMATICAS")
        print("-" * 100)
        vagas_problema = [1193, 1196, 1205, 1207, 1212, 1211]

        for vaga_id in vagas_problema:
            cursor.execute("""
                SELECT v.id, v.name, v.inhire_id,
                       r.id as req_id, r.name as req_name
                FROM vagas v
                LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
                WHERE v.id = %s
            """, (vaga_id,))
            row = cursor.fetchone()

            if row:
                print(f"\nVaga {row[0]}: {row[1][:50]}")
                if row[3]:
                    print(f"  [OK] TEM REQUISICAO! Req {row[3]}: {row[4][:50] if row[4] else 'NULL'}")
                else:
                    print(f"  [X] SEM REQUISICAO!")

        cursor.close()
        conn.close()

        print("\n" + "=" * 100)
        print("VALIDACAO CONCLUIDA")
        print("=" * 100)

    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
