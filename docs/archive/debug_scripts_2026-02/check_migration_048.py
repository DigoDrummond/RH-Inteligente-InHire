import psycopg2

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("VERIFICAÇÃO DA MIGRATION 048")
print("=" * 80)

# Verificar colunas de vw_analise_posicoes
print("\n1. VIEW: vw_analise_posicoes")
print("-" * 80)
cur.execute("""
    SELECT ordinal_position, column_name
    FROM information_schema.columns
    WHERE table_name = 'vw_analise_posicoes'
    ORDER BY ordinal_position
""")

columns = cur.fetchall()
print(f"Total de colunas: {len(columns)}\n")

# Mostrar colunas próximas ao campo responsavel
for pos, name in columns:
    if 15 <= pos <= 19:
        marker = " <-- NOVO" if name == 'email_responsavel_cliente' else ""
        print(f"  {pos:2}. {name}{marker}")

# Verificar se email_responsavel_cliente existe
email_col_exists = any(name == 'email_responsavel_cliente' for _, name in columns)
print(f"\nCampo 'email_responsavel_cliente' existe? {'SIM' if email_col_exists else 'NÃO'}")

# Verificar colunas de vw_dados_jade
print("\n2. VIEW: vw_dados_jade")
print("-" * 80)
cur.execute("""
    SELECT ordinal_position, column_name
    FROM information_schema.columns
    WHERE table_name = 'vw_dados_jade'
    ORDER BY ordinal_position
""")

columns_jade = cur.fetchall()
print(f"Total de colunas: {len(columns_jade)}\n")

# Mostrar colunas próximas ao campo responsavel_requisicao
for pos, name in columns_jade:
    if 13 <= pos <= 17:
        marker = " <-- NOVO" if name == 'email_responsavel_cliente' else ""
        print(f"  {pos:2}. {name}{marker}")

# Verificar se email_responsavel_cliente existe
email_col_jade = any(name == 'email_responsavel_cliente' for _, name in columns_jade)
print(f"\nCampo 'email_responsavel_cliente' existe? {'SIM' if email_col_jade else 'NÃO'}")

# Testar se o campo retorna dados
print("\n3. TESTE DE DADOS")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*) as total,
           COUNT(email_responsavel_cliente) as com_email
    FROM vw_analise_posicoes
""")
total, com_email = cur.fetchone()
print(f"vw_analise_posicoes: {total} registros, {com_email} com email ({100*com_email/total if total > 0 else 0:.1f}%)")

cur.execute("""
    SELECT COUNT(*) as total,
           COUNT(email_responsavel_cliente) as com_email
    FROM vw_dados_jade
""")
total_jade, com_email_jade = cur.fetchone()
print(f"vw_dados_jade: {total_jade} registros, {com_email_jade} com email ({100*com_email_jade/total_jade if total_jade > 0 else 0:.1f}%)")

print("\n" + "=" * 80)
print("CONCLUSÃO:")
print("=" * 80)

if email_col_exists and email_col_jade:
    print("✓ Migration 048 FOI APLICADA com sucesso!")
    print("  - Campo 'email_responsavel_cliente' existe em ambas as views")
else:
    print("✗ Migration 048 NÃO foi aplicada")
    print(f"  - vw_analise_posicoes: {'OK' if email_col_exists else 'FALTANDO'}")
    print(f"  - vw_dados_jade: {'OK' if email_col_jade else 'FALTANDO'}")

print("=" * 80)

cur.close()
conn.close()
