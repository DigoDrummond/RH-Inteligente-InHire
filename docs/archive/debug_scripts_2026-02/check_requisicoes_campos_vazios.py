"""
Script para verificar campos vazios na tabela requisicoes
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

        # 1. Verificar estrutura da tabela
        print("=" * 80)
        print("1. ESTRUTURA DA TABELA REQUISICOES")
        print("=" * 80)
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'requisicoes'
            ORDER BY ordinal_position
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]:30s} {row[1]:20s} NULL={row[2]}")

        # 2. Total de registros
        print("\n" + "=" * 80)
        print("2. CONTAGEM DE REGISTROS")
        print("=" * 80)
        cursor.execute("SELECT COUNT(*) FROM requisicoes")
        total = cursor.fetchone()[0]
        print(f"  Total de registros: {total}")

        # 3. Verificar campos preenchidos vs vazios
        print("\n" + "=" * 80)
        print("3. COBERTURA DE DADOS (campos preenchidos vs vazios)")
        print("=" * 80)

        campos = ['id', 'name', 'vaga_id', 'status', 'user_name', 'requester_name',
                  'approver_name', 'position_amount', 'salary_min', 'salary_max',
                  'created_at', 'updated_at']

        for campo in campos:
            cursor.execute(f"SELECT COUNT(*) FROM requisicoes WHERE {campo} IS NOT NULL")
            preenchidos = cursor.fetchone()[0]
            vazios = total - preenchidos
            pct = (preenchidos / total * 100) if total > 0 else 0
            print(f"  {campo:30s}: {preenchidos:4d}/{total:4d} ({pct:5.1f}%) | {vazios} vazios")

        # 4. Verificar custom_fields
        print("\n" + "=" * 80)
        print("4. CUSTOM_FIELDS (JSONB)")
        print("=" * 80)
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE custom_fields IS NULL) as nulls,
                COUNT(*) FILTER (WHERE custom_fields::text = '{}') as vazios,
                COUNT(*) FILTER (WHERE custom_fields IS NOT NULL AND custom_fields::text != '{}') as preenchidos
            FROM requisicoes
        """)
        row = cursor.fetchone()
        print(f"  NULL:        {row[0]} ({row[0]/total*100:.1f}%)")
        print(f"  Vazio ({{}}):  {row[1]} ({row[1]/total*100:.1f}%)")
        print(f"  Preenchido:  {row[2]} ({row[2]/total*100:.1f}%)")

        # 5. Exemplos de registros
        print("\n" + "=" * 80)
        print("5. EXEMPLOS DE REGISTROS (10 primeiros)")
        print("=" * 80)
        cursor.execute("""
            SELECT id, name, vaga_id, status, user_name, requester_name, position_amount,
                   CASE
                       WHEN custom_fields IS NULL THEN 'NULL'
                       WHEN custom_fields::text IN ('{}', 'null', '[]') THEN 'VAZIO'
                       ELSE 'PREENCHIDO'
                   END as cf_status
            FROM requisicoes
            ORDER BY id
            LIMIT 10
        """)
        print(f"{'ID':<8} {'Name':<30} {'Vaga':<8} {'Status':<15} {'User':<20} {'Requester':<20} {'Amt':<5} {'CF':<12}")
        print("-" * 130)
        for row in cursor.fetchall():
            nome = (row[1] or "NULL")[:29]
            user = (row[4] or "NULL")[:19]
            requester = (row[5] or "NULL")[:19]
            print(f"{row[0]:<8} {nome:<30} {row[2] or 'NULL':<8} {row[3] or 'NULL':<15} {user:<20} {requester:<20} {row[6] or 'N':<5} {row[7]:<12}")

        # 6. Verificar a origem dos dados
        print("\n" + "=" * 80)
        print("6. ORIGEM DOS DADOS")
        print("=" * 80)
        cursor.execute("SELECT COUNT(*) FROM posicoes")
        posicoes_total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM vagas")
        vagas_total = cursor.fetchone()[0]

        print(f"  Tabela posicoes: {posicoes_total} registros")
        print(f"  Tabela vagas:    {vagas_total} registros")
        print(f"  Tabela requisicoes: {total} registros")
        print("\n  ANÁLISE: A tabela requisicoes deve ser preenchida a partir da API /requisitions")
        print("           mas pode ter relação com posicoes e vagas via vaga_id")

        # 7. Verificar se há algum padrão nos vazios
        print("\n" + "=" * 80)
        print("7. PADRÃO NOS REGISTROS COM CAMPOS VAZIOS")
        print("=" * 80)
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE name IS NULL) as name_null,
                COUNT(*) FILTER (WHERE vaga_id IS NULL) as vaga_id_null,
                COUNT(*) FILTER (WHERE user_name IS NULL) as user_name_null,
                COUNT(*) FILTER (WHERE requester_name IS NULL) as requester_name_null,
                COUNT(*) FILTER (WHERE approver_name IS NULL) as approver_name_null,
                COUNT(*) FILTER (WHERE position_amount IS NULL) as position_amount_null,
                COUNT(*) FILTER (WHERE salary_min IS NULL) as salary_min_null,
                COUNT(*) FILTER (WHERE salary_max IS NULL) as salary_max_null,
                COUNT(*) FILTER (WHERE custom_fields IS NULL OR custom_fields::text IN ('{}', 'null', '[]')) as custom_fields_empty
            FROM requisicoes
        """)
        row = cursor.fetchone()
        print(f"  Total de requisicoes:    {row[0]}")
        print(f"  Sem name:                {row[1]} ({row[1]/row[0]*100:.1f}%)")
        print(f"  Sem vaga_id:             {row[2]} ({row[2]/row[0]*100:.1f}%)")
        print(f"  Sem user_name:           {row[3]} ({row[3]/row[0]*100:.1f}%)")
        print(f"  Sem requester_name:      {row[4]} ({row[4]/row[0]*100:.1f}%)")
        print(f"  Sem approver_name:       {row[5]} ({row[5]/row[0]*100:.1f}%)")
        print(f"  Sem position_amount:     {row[6]} ({row[6]/row[0]*100:.1f}%)")
        print(f"  Sem salary_min:          {row[7]} ({row[7]/row[0]*100:.1f}%)")
        print(f"  Sem salary_max:          {row[8]} ({row[8]/row[0]*100:.1f}%)")
        print(f"  Custom_fields vazio:     {row[9]} ({row[9]/row[0]*100:.1f}%)")

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
