"""
Script para verificar o conteúdo de custom_fields na tabela requisicoes
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

        print("=" * 80)
        print("ANÁLISE DE CUSTOM_FIELDS NA TABELA REQUISICOES")
        print("=" * 80)

        # Buscar exemplos de custom_fields
        cursor.execute("""
            SELECT id, name, custom_fields
            FROM requisicoes
            WHERE custom_fields IS NOT NULL
              AND custom_fields::text NOT IN ('{}', 'null', '[]')
            ORDER BY id
            LIMIT 5
        """)

        rows = cursor.fetchall()

        print(f"\nTotal de exemplos: {len(rows)}\n")

        for row in rows:
            print("-" * 80)
            print(f"ID: {row[0]}")
            print(f"Name: {row[1]}")
            print(f"Custom Fields:")
            if row[2]:
                try:
                    cf_dict = row[2] if isinstance(row[2], dict) else json.loads(row[2])
                    print(json.dumps(cf_dict, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f"  ERRO ao parsear: {e}")
                    print(f"  Raw: {row[2]}")
            print()

        # Verificar quais chaves existem nos custom_fields
        print("=" * 80)
        print("CHAVES DISPONÍVEIS NOS CUSTOM_FIELDS")
        print("=" * 80)
        cursor.execute("""
            WITH field_keys AS (
                SELECT
                    id,
                    jsonb_object_keys(custom_fields::jsonb) as key
                FROM requisicoes
                WHERE custom_fields IS NOT NULL
                  AND custom_fields::text NOT IN ('{}', 'null', '[]')
            )
            SELECT key, COUNT(*) as freq
            FROM field_keys
            GROUP BY key
            ORDER BY freq DESC
        """)

        print(f"\n{'Chave':<40} {'Frequência':>10}")
        print("-" * 52)
        for row in cursor.fetchall():
            print(f"{row[0]:<40} {row[1]:>10}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 80)
        print("ANÁLISE CONCLUÍDA")
        print("=" * 80)

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
