"""
Investigar como o campo vaga_id está sendo preenchido nas requisições
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
        print("INVESTIGAÇÃO: COMO vaga_id É VINCULADO NAS REQUISIÇÕES")
        print("=" * 100)

        # 1. Estatísticas de vaga_id nas requisições
        print("\n1. ESTATÍSTICAS DE vaga_id NA TABELA REQUISICOES")
        print("-" * 100)
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(vaga_id) as com_vaga_id,
                COUNT(*) - COUNT(vaga_id) as sem_vaga_id,
                COUNT(DISTINCT vaga_id) as vagas_unicas
            FROM requisicoes
        """)
        row = cursor.fetchone()
        print(f"Total de requisições:           {row[0]}")
        print(f"Com vaga_id preenchido:         {row[1]} ({row[1]/row[0]*100:.1f}%)")
        print(f"Com vaga_id NULL:               {row[2]} ({row[2]/row[0]*100:.1f}%)")
        print(f"Vagas únicas linkadas:          {row[3]}")

        # 2. Verificar como job_inhire_id está preenchido
        print("\n2. ESTATÍSTICAS DE job_inhire_id")
        print("-" * 100)
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(job_inhire_id) as com_job_id,
                COUNT(*) - COUNT(job_inhire_id) as sem_job_id
            FROM requisicoes
        """)
        row = cursor.fetchone()
        print(f"Total de requisições:           {row[0]}")
        print(f"Com job_inhire_id preenchido:   {row[1]} ({row[1]/row[0]*100:.1f}%)")
        print(f"Com job_inhire_id NULL:         {row[2]} ({row[2]/row[0]*100:.1f}%)")

        # 3. Tentar fazer match manual entre requisicoes.job_inhire_id e vagas.inhire_id
        print("\n3. VERIFICANDO MATCH ENTRE job_inhire_id E vagas.inhire_id")
        print("-" * 100)
        cursor.execute("""
            SELECT COUNT(*)
            FROM requisicoes r
            INNER JOIN vagas v ON r.job_inhire_id = v.inhire_id
            WHERE r.vaga_id IS NULL
        """)
        match_disponiveis = cursor.fetchone()[0]
        print(f"Requisições com vaga_id NULL que TÊM match via job_inhire_id: {match_disponiveis}")

        if match_disponiveis > 0:
            print("\n[PROBLEMA ENCONTRADO] Há requisições que poderiam estar linkadas mas vaga_id está NULL!")
            print("\nExemplos:")
            cursor.execute("""
                SELECT r.id, r.name, r.job_inhire_id, v.id as vaga_id, v.name as vaga_name
                FROM requisicoes r
                INNER JOIN vagas v ON r.job_inhire_id = v.inhire_id
                WHERE r.vaga_id IS NULL
                LIMIT 10
            """)
            for row in cursor.fetchall():
                print(f"  Req {row[0]}: {(row[1] or 'NULL')[:50]}")
                print(f"    job_inhire_id: {row[2]}")
                print(f"    Deveria linkar com Vaga {row[3]}: {(row[4] or 'NULL')[:50]}")
                print()

        # 4. Verificar as 6 vagas problemáticas especificamente
        print("\n4. VERIFICANDO AS 6 VAGAS PROBLEMÁTICAS")
        print("-" * 100)
        vagas_problema = [1193, 1196, 1205, 1207, 1212, 1211]

        for vaga_id in vagas_problema:
            cursor.execute("""
                SELECT v.id, v.name, v.inhire_id,
                       r.id, r.name, r.job_inhire_id
                FROM vagas v
                LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
                WHERE v.id = %s
            """, (vaga_id,))
            row = cursor.fetchone()

            if row[3]:  # tem requisição via job_inhire_id
                print(f"\n[OK] Vaga {row[0]}: {row[1][:50]}")
                print(f"  Vaga inhire_id: {row[2]}")
                print(f"  Requisição encontrada via job_inhire_id:")
                print(f"    Req ID: {row[3]}")
                print(f"    Req Nome: {row[4][:50]}")
                print(f"    Req job_inhire_id: {row[5]}")

                # Verificar se vaga_id está NULL
                cursor.execute("SELECT vaga_id FROM requisicoes WHERE id = %s", (row[3],))
                vaga_id_atual = cursor.fetchone()[0]
                if vaga_id_atual is None:
                    print(f"    [PROBLEMA] vaga_id está NULL! Precisa ser {vaga_id}")
                elif vaga_id_atual != vaga_id:
                    print(f"    [PROBLEMA] vaga_id está errado! É {vaga_id_atual}, deveria ser {vaga_id}")
                else:
                    print(f"    [OK] vaga_id está correto: {vaga_id_atual}")
            else:
                print(f"\n[X] Vaga {row[0]}: {row[1][:50]}")
                print(f"  Vaga inhire_id: {row[2]}")
                print(f"  NENHUMA requisição encontrada via job_inhire_id")

                # Verificar se existe requisição com nome parecido
                cursor.execute("""
                    SELECT id, name, job_inhire_id, vaga_id
                    FROM requisicoes
                    WHERE LOWER(name) LIKE %s
                """, (f"%{row[1].lower()[:30]}%",))
                similar = cursor.fetchall()
                if similar:
                    print(f"  Requisições com nome similar:")
                    for sim in similar[:3]:
                        print(f"    Req {sim[0]}: {sim[1][:50]}")
                        print(f"      job_inhire_id: {sim[2]}")
                        print(f"      vaga_id: {sim[3]}")

        # 5. Verificar requisições recentes sem vaga_id
        print("\n5. ÚLTIMAS 20 REQUISIÇÕES SEM vaga_id")
        print("-" * 100)
        cursor.execute("""
            SELECT id, name, job_inhire_id, inhire_id, created_at
            FROM requisicoes
            WHERE vaga_id IS NULL
            ORDER BY created_at DESC
            LIMIT 20
        """)
        print(f"{'ID':<6} {'Nome':<50} {'job_inhire_id':<40} {'Criada':<20}")
        print("-" * 120)
        for row in cursor.fetchall():
            print(f"{row[0]:<6} {row[1][:49]:<50} {str(row[2] or 'NULL'):<40} {str(row[4])[:19]:<20}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 100)
        print("INVESTIGAÇÃO CONCLUÍDA")
        print("=" * 100)

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
