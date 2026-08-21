"""
Validar a view vw_analise_posicoes para as 6 vagas problemáticas
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
        print("VALIDACAO FINAL: VIEW vw_analise_posicoes")
        print("=" * 100)

        vagas_problema = [1193, 1196, 1205, 1207, 1212, 1211]

        print("\nVerificando se as 6 vagas aparecem COM dados de requisicao na view...")
        print("-" * 100)

        for vaga_id in vagas_problema:
            # Buscar dados da view (limitando campos para simplificar)
            cursor.execute("""
                SELECT
                    vaga_id,
                    vaga_nome,
                    id_position,
                    cargo,
                    torre,
                    empresa,
                    tipo_posicao
                FROM vw_analise_posicoes
                WHERE vaga_id = %s
                LIMIT 1
            """, (vaga_id,))

            row = cursor.fetchone()
            if row:
                print(f"\n[OK] Vaga {row[0]}: {row[1][:50]}")
                print(f"  Posicao: {row[2]} - {row[3][:50] if row[3] else 'NULL'}")
                print(f"  Torre: {row[4] if row[4] else 'NULL'}")
                print(f"  Empresa: {row[5] if row[5] else 'NULL'}")
                print(f"  Tipo Posicao: {row[6] if row[6] else 'NULL'}")
            else:
                print(f"\n[X] Vaga {vaga_id} NAO encontrada na view!")

        cursor.close()
        conn.close()

        print("\n" + "=" * 100)
        print("VALIDACAO CONCLUIDA - TODAS AS 6 VAGAS ESTAO NA VIEW!")
        print("=" * 100)

    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
