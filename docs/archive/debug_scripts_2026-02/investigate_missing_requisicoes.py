"""
Investigar por que posições recentes não têm dados de requisicoes
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

        # Vagas problemáticas reportadas pelo usuário
        vagas_problema = [1193, 1196, 1205, 1207, 1212, 1211]

        print("=" * 100)
        print("INVESTIGAÇÃO: POSIÇÕES SEM DADOS DE REQUISICOES")
        print("=" * 100)

        # 1. Verificar se essas vagas existem na tabela vagas
        print("\n1. VERIFICANDO SE AS VAGAS EXISTEM")
        print("-" * 100)
        cursor.execute(f"""
            SELECT id, name, inhire_id, created_at, updated_at
            FROM vagas
            WHERE id IN ({','.join(map(str, vagas_problema))})
            ORDER BY id
        """)
        vagas = cursor.fetchall()
        print(f"Vagas encontradas: {len(vagas)}/{len(vagas_problema)}")
        for row in vagas:
            print(f"  Vaga {row[0]}: {row[1][:50]} | Inhire ID: {row[2]} | Criada: {row[3]}")

        # 2. Verificar se essas vagas têm requisicoes
        print("\n2. VERIFICANDO REQUISICOES PARA ESSAS VAGAS")
        print("-" * 100)
        cursor.execute(f"""
            SELECT r.id, r.name, r.vaga_id, r.inhire_id, r.status, r.created_at
            FROM requisicoes r
            WHERE r.vaga_id IN ({','.join(map(str, vagas_problema))})
            ORDER BY r.vaga_id
        """)
        requisicoes = cursor.fetchall()
        print(f"Requisições encontradas: {len(requisicoes)}")
        if requisicoes:
            for row in requisicoes:
                print(f"  Req {row[0]}: {row[1][:50]} | Vaga {row[2]} | Status: {row[4]}")
        else:
            print("  NENHUMA REQUISIÇÃO ENCONTRADA para essas vagas!")

        # 3. Verificar se essas vagas têm posicoes
        print("\n3. VERIFICANDO POSIÇÕES PARA ESSAS VAGAS")
        print("-" * 100)
        cursor.execute(f"""
            SELECT p.id, p.vaga_id, p.cargo, p.created_at
            FROM posicoes p
            WHERE p.vaga_id IN ({','.join(map(str, vagas_problema))})
            ORDER BY p.vaga_id
        """)
        posicoes = cursor.fetchall()
        print(f"Posições encontradas: {len(posicoes)}")
        for row in posicoes:
            print(f"  Posição {row[0]}: {row[2][:50]} | Vaga {row[1]}")

        # 4. Verificar a relação entre vagas e requisicoes (todas)
        print("\n4. ESTATÍSTICAS GERAIS DE VAGAS x REQUISICOES")
        print("-" * 100)
        cursor.execute("""
            SELECT
                COUNT(DISTINCT v.id) as total_vagas,
                COUNT(DISTINCT r.vaga_id) as vagas_com_requisicao,
                COUNT(DISTINCT v.id) - COUNT(DISTINCT r.vaga_id) as vagas_sem_requisicao
            FROM vagas v
            LEFT JOIN requisicoes r ON r.vaga_id = v.id
        """)
        row = cursor.fetchone()
        print(f"  Total de vagas:            {row[0]}")
        print(f"  Vagas com requisição:      {row[1]} ({row[1]/row[0]*100:.1f}%)")
        print(f"  Vagas SEM requisição:      {row[2]} ({row[2]/row[0]*100:.1f}%)")

        # 5. Verificar vagas recentes sem requisicao
        print("\n5. ÚLTIMAS 20 VAGAS SEM REQUISIÇÃO")
        print("-" * 100)
        cursor.execute("""
            SELECT v.id, v.name, v.inhire_id, v.created_at,
                   CASE WHEN r.vaga_id IS NULL THEN 'SEM REQ' ELSE 'COM REQ' END as tem_req
            FROM vagas v
            LEFT JOIN requisicoes r ON r.vaga_id = v.id
            WHERE r.vaga_id IS NULL
            ORDER BY v.created_at DESC
            LIMIT 20
        """)
        print(f"{'ID':<8} {'Nome':<60} {'Inhire ID':<40} {'Criada':<20}")
        print("-" * 130)
        for row in cursor.fetchall():
            print(f"{row[0]:<8} {row[1][:59]:<60} {row[2]:<40} {str(row[3]):<20}")

        # 6. Verificar se há requisitions na API que não foram sincronizadas
        print("\n6. ANÁLISE DO PROBLEMA")
        print("-" * 100)
        print("POSSÍVEIS CAUSAS:")
        print("  1. As vagas foram criadas ANTES do sistema de sync de requisições")
        print("  2. As requisições dessas vagas não existem no InHire")
        print("  3. O endpoint /requisitions não retorna essas requisições")
        print("  4. Há um job_inhire_id diferente que não conseguimos mapear")

        # 7. Verificar o job_inhire_id das vagas problemáticas
        print("\n7. VERIFICANDO JOB_INHIRE_ID DAS VAGAS PROBLEMÁTICAS")
        print("-" * 100)
        cursor.execute(f"""
            SELECT v.id, v.name, v.inhire_id as vaga_inhire_id
            FROM vagas v
            WHERE v.id IN ({','.join(map(str, vagas_problema))})
            ORDER BY v.id
        """)
        print(f"{'Vaga ID':<10} {'Vaga Inhire ID':<40} {'Nome':<50}")
        print("-" * 100)
        for row in cursor.fetchall():
            print(f"{row[0]:<10} {row[1]:<40} {row[2][:49]}")

        # 8. Verificar se existe alguma requisição com job_inhire_id dessas vagas
        print("\n8. BUSCANDO REQUISIÇÕES POR JOB_INHIRE_ID")
        print("-" * 100)
        cursor.execute(f"""
            SELECT v.id as vaga_id, v.inhire_id as vaga_inhire_id,
                   r.id as req_id, r.job_inhire_id, r.name as req_name
            FROM vagas v
            LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
            WHERE v.id IN ({','.join(map(str, vagas_problema))})
            ORDER BY v.id
        """)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                if row[2]:  # tem requisição
                    print(f"  ✓ Vaga {row[0]} TEM requisição {row[2]}: {row[4]}")
                else:
                    print(f"  ✗ Vaga {row[0]} (inhire_id: {row[1]}) NÃO TEM requisição correspondente")

        # 9. Total de requisições vs total de vagas
        print("\n9. ESTATÍSTICAS FINAIS")
        print("-" * 100)
        cursor.execute("SELECT COUNT(*) FROM vagas")
        total_vagas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM requisicoes")
        total_req = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT vaga_id) FROM requisicoes WHERE vaga_id IS NOT NULL")
        vagas_linkadas = cursor.fetchone()[0]

        print(f"  Total de vagas no sistema:           {total_vagas}")
        print(f"  Total de requisições sincronizadas:  {total_req}")
        print(f"  Vagas linkadas com requisições:      {vagas_linkadas} ({vagas_linkadas/total_vagas*100:.1f}%)")
        print(f"  Requisições sem vaga_id:             {total_req - vagas_linkadas}")

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
