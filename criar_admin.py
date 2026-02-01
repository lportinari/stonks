import sqlite3
import bcrypt

# Conectar ao banco de dados
conn = sqlite3.connect('database/stocks.db')
cursor = conn.cursor()

# Criar usuário admin
nome = "Administrador"
email = "admin@stonks.com"
senha = "admin123"

# Hash da senha
senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Inserir usuário admin
cursor.execute('''
    INSERT INTO users (nome, email, senha_hash, email_verificado, ativo)
    VALUES (?, ?, ?, ?, ?)
''', (nome, email, senha_hash, True, True))

# Confirmar mudanças
conn.commit()
conn.close()

print('✅ Usuário admin criado com sucesso!')
print('📧 Email: admin@stonks.com')
print('🔑 Senha: admin123')
print('🚀 Acesse: http://localhost:5000/auth/login')