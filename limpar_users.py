import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('database/stocks.db')
cursor = conn.cursor()

# Limpar tabela de usuários
cursor.execute('DELETE FROM users')
cursor.execute('DELETE FROM sqlite_sequence WHERE name="users"')

# Confirmar mudanças
conn.commit()
conn.close()

print('✅ Tabela users limpa com sucesso!')
print('✅ Sequence resetada!')
print('🚀 Agora é possível criar novos usuários!')