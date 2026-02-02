import sqlite3
import bcrypt

# Conectar ao banco de dados
conn = sqlite3.connect('database/stocks.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Buscar usuário pelo email
email = "lvp.celinski@gmail.com"
cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
user = cursor.fetchone()

if user:
    print(f"✅ Usuário encontrado: {user['nome']}")
    print(f"📧 Email: {user['email']}")
    print(f"🔐 Email verificado: {user['email_verificado']}")
    print(f"🟢 Ativo: {user['ativo']}")
    
    # Verificar senha
    senha_teste = "admin123"
    senha_hash = user['senha_hash']
    
    if bcrypt.checkpw(senha_teste.encode('utf-8'), senha_hash.encode('utf-8')):
        print("✅ Senha está correta!")
        
        # Forçar verificação do email
        cursor.execute('UPDATE users SET email_verificado = 1 WHERE email = ?', (email,))
        conn.commit()
        print("✅ Email verificado com sucesso!")
        
    else:
        print("❌ Senha está incorreta!")
else:
    print("❌ Usuário não encontrado!")

# Listar todos os usuários
print("\n📋 Todos os usuários cadastrados:")
cursor.execute('SELECT id, nome, email, email_verificado, ativo FROM users')
users = cursor.fetchall()

for user in users:
    status = "✅" if user['email_verificado'] and user['ativo'] else "❌"
    print(f"  {status} ID:{user['id']} - {user['nome']} ({user['email']}) - Verificado:{user['email_verificado']} Ativo:{user['ativo']}")

conn.close()