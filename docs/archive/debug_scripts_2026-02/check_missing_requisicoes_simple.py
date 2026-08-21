"""
Verificação simples: Por que vagas recentes não têm requisições?
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

        vagas_problema = [1193, 1196, 1205, 1207, 1212, 1211]

        print("=" * 100)
        print("DIAGNÓSTICO: VAGAS SEM REQUISIÇÕES")
        print("=" * 100)

        # 1. Confirmar que essas vagas não têm requisições
        print("\n1. VAGAS REPORTADAS PELO USUÁRIO")
        print("-" * 100)
        for vaga_id in vagas_problema:
            cursor.execute("""
                SELECT v.id, v.name, v.inhire_id as vaga_inhire_id, v.created_at,
                       r.id as req_id, r.inhire_id as req_inhire_id
                FROM vagas v
                LEFT JOIN requisicoes r ON r.vaga_id = v.id
                WHERE v.id = %s
            """, (vaga_id,))
            row = cursor.fetchone()
            status = "[OK] TEM REQ" if row[4] else "[X] SEM REQ"
            print(f"  Vaga {row[0]:4d}: {status} | {row[1][:60]}")
            print(f"            Vaga Inhire ID: {row[2]}")
            print(f"            Criada em: {row[3]}")
            if row[4]:
                print(f"            Requisição ID: {row[4]} (Inhire: {row[5]})")
            print()

        # 2. Estatísticas gerais
        print("\n2. ESTATÍSTICAS GERAIS")
        print("-" * 100)
        cursor.execute("""
            SELECT
                COUNT(*) as total_vagas,
                COUNT(DISTINCT r.vaga_id) as vagas_com_req,
                COUNT(*) - COUNT(DISTINCT r.vaga_id) as vagas_sem_req
            FROM vagas v
            LEFT JOIN requisicoes r ON r.vaga_id = v.id
        """)
        row = cursor.fetchone()
        print(f"  Total de vagas:        {row[0]}")
        print(f"  Com requisição:        {row[1]} ({row[1]/row[0]*100:.1f}%)")
        print(f"  SEM requisição:        {row[2]} ({row[2]/row[0]*100:.1f}%)")

        # 3. Quando essas vagas foram criadas vs quando a requisição foi sincronizada
        print("\n3. ÚLTIMAS 30 VAGAS CRIADAS (para comparar)")
        print("-" * 100)
        cursor.execute("""
            SELECT v.id, v.name, v.created_at,
                   CASE WHEN r.vaga_id IS NOT NULL THEN 'SIM' ELSE 'NÃO' END as tem_req
            FROM vagas v
            LEFT JOIN requisicoes r ON r.vaga_id = v.id
            ORDER BY v.created_at DESC
            LIMIT 30
        """)
        print(f"{'ID':<6} {'Tem Req':<10} {'Criada em':<20} {'Nome':<60}")
        print("-" * 100)
        for row in cursor.fetchall():
            print(f"{row[0]:<6} {row[3]:<10} {str(row[2])[:19]:<20} {row[1][:59]}")

        # 4. Quando foi a última sincronização de requisições?
        print("\n4. ÚLTIMA ATUALIZAÇÃO DE DADOS")
        print("-" * 100)
        cursor.execute("SELECT MAX(updated_at) FROM requisicoes")
        ultima_req = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(updated_at) FROM vagas")
        ultima_vaga = cursor.fetchone()[0]

        print(f"  Última atualização de requisições: {ultima_req}")
        print(f"  Última atualização de vagas:       {ultima_vaga}")

        # 5. Verificar se há job_inhire_id correspondente
        print("\n5. TENTANDO MATCH POR JOB_INHIRE_ID")
        print("-" * 100)
        for vaga_id in vagas_problema:
            cursor.execute("""
                SELECT v.id, v.inhire_id,
                       (SELECT COUNT(*) FROM requisicoes WHERE job_inhire_id = v.inhire_id) as match_count
                FROM vagas v
                WHERE v.id = %s
            """, (vaga_id,))
            row = cursor.fetchone()
            if row[2] > 0:
                print(f"  [OK] Vaga {row[0]} encontrou {row[2]} requisicao(oes) via job_inhire_id")
            else:
                print(f"  [X] Vaga {row[0]} nao encontrou requisicao via job_inhire_id")

        # 6. CONCLUSÃO
        print("\n" + "=" * 100)
        print("CONCLUSÕES")
        print("=" * 100)
        print()
        print("PROBLEMA IDENTIFICADO:")
        print("  As vagas recentes (criadas em fevereiro/2026) NÃO têm requisições correspondentes.")
        print()
        print("POSSÍVEIS CAUSAS:")
        print("  1. O endpoint /requisitions não retorna essas requisições")
        print("  2. Essas vagas foram criadas sem requisição formal no InHire")
        print("  3. O relacionamento vaga_id não está sendo populado corretamente")
        print("  4. As requisições dessas vagas ainda não foram sincronizadas")
        print()
        print("PRÓXIMAS AÇÕES:")
        print("  1. Verificar manualmente se essas vagas têm requisições no InHire")
        print("  2. Testar o endpoint /requisitions para essas vagas específicas")
        print("  3. Verificar o código de sync de requisições")
        print("  4. Sincronizar novamente as requisições")
        print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
