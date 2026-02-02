import sqlite3
import bcrypt

# Conectar ao banco de dados
conn = sqlite3.connect('database/stocks.db')
cursor = conn.cursor()

# Email do usuário e nova senha
email = "lvp.celinski@gmail.com"
nova_senha = "admin123"

# Gerar novo hash da senha
senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Atualizar senha
cursor.execute('UPDATE users SET senha_hash = ? WHERE email = ?', (senha_hash, email))
conn.commit()

# Verificar se funcionou
cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
user = cursor.fetchone()

if user:
    print(f"✅ Senha atualizada com sucesso!")
    print(f"👤 Usuário: {user[1]}")
    print(f"📧 Email: {user[2]}")
    
    # Testar a nova senha
    if bcrypt.checkpw(nova_senha.encode('utf-8'), user[3].encode('utf-8')):
        print("✅ Nova senha verificada com sucesso!")
        print(f"🔑 Senha: {nova_senha}")
        print("🚀 Agora você pode fazer login!")
    else:
        print("❌ Erro na verificação da senha!")
else:
    print("❌ Usuário não encontrado!")

conn.close()