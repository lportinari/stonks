#!/usr/bin/env python3
"""
Script de inicialização do banco de dados
Cria todas as tabelas necessárias para a aplicação
"""

import sqlite3
import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_tables():
    """Cria todas as tabelas do banco de dados"""
    
    # Caminho do banco de dados
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'stocks.db')
    
    print(f"Inicializando banco de dados: {db_path}")
    
    # Criar diretório se não existir
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                email_verificado BOOLEAN DEFAULT FALSE,
                token_verificacao VARCHAR(255),
                token_reset_senha VARCHAR(255),
                token_expiracao DATETIME,
                data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
                ultimo_login DATETIME,
                ativo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Tabela de compras de ativos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker VARCHAR(10) NOT NULL,
                nome_ativo VARCHAR(200) NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                taxas REAL DEFAULT 0.0,
                custo_total REAL NOT NULL,
                preco_medio REAL NOT NULL,
                data_compra DATE NOT NULL,
                quantidade_vendida INTEGER DEFAULT 0,
                preco_venda REAL,
                data_venda DATE,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Índices para melhor performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON purchases(user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_purchases_ticker ON purchases(ticker)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_purchases_data_compra ON purchases(data_compra)
        ''')
        
        # Tabela de logs de preços (opcional, para histórico)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                preco REAL NOT NULL,
                data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                fonte VARCHAR(50) DEFAULT 'manual'
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_history_ticker ON price_history(ticker)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_history_data ON price_history(data_hora)
        ''')
        
        # Inserir usuário administrador padrão (se não existir)
        cursor.execute('''
            SELECT COUNT(*) FROM users WHERE email = 'admin@stonks.com'
        ''')
        
        if cursor.fetchone()[0] == 0:
            import bcrypt
            senha_admin = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute('''
                INSERT INTO users (nome, email, senha_hash, email_verificado)
                VALUES (?, ?, ?, ?)
            ''', ('Administrador', 'admin@stonks.com', senha_admin, True))
            
            print("✓ Usuário administrador criado: admin@stonks.com / admin123")
        
        # Commit das alterações
        conn.commit()
        
        print("✓ Tabelas criadas com sucesso!")
        print("\nTabelas criadas:")
        print("- users (usuários)")
        print("- purchases (compras de ativos)")
        print("- price_history (histórico de preços)")
        
    except Exception as e:
        print(f"✗ Erro ao criar tabelas: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
    
    return True

def check_existing_data():
    """Verifica se já existem dados no banco"""
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'stocks.db')
    
    if not os.path.exists(db_path):
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela stocks existe (dados antigos)
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='stocks'
        ''')
        
        if cursor.fetchone():
            print("✓ Tabela 'stocks' encontrada (dados antigos)")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Erro ao verificar dados existentes: {e}")
        return False
    
    finally:
        conn.close()

def add_new_tables():
    """Adiciona apenas as novas tabelas sem perder dados existentes"""
    
    # Caminho do banco de dados
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'stocks.db')
    
    print(f"Adicionando novas tabelas ao banco: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela users já existe
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        ''')
        
        if not cursor.fetchone():
            # Criar tabela de usuários
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    senha_hash VARCHAR(255) NOT NULL,
                    email_verificado BOOLEAN DEFAULT FALSE,
                    token_verificacao VARCHAR(255),
                    token_reset_senha VARCHAR(255),
                    token_expiracao DATETIME,
                    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ultimo_login DATETIME,
                    ativo BOOLEAN DEFAULT TRUE
                )
            ''')
            print("✓ Tabela 'users' criada")
            
            # Inserir usuário administrador
            import bcrypt
            senha_admin = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute('''
                INSERT INTO users (nome, email, senha_hash, email_verificado)
                VALUES (?, ?, ?, ?)
            ''', ('Administrador', 'admin@stonks.com', senha_admin, True))
            
            print("✓ Usuário administrador criado: admin@stonks.com / admin123")
        else:
            print("✓ Tabela 'users' já existe")
        
        # Verificar se a tabela purchases já existe
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='purchases'
        ''')
        
        if not cursor.fetchone():
            # Criar tabela de compras
            cursor.execute('''
                CREATE TABLE purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ticker VARCHAR(10) NOT NULL,
                    nome_ativo VARCHAR(200) NOT NULL,
                    quantidade INTEGER NOT NULL,
                    preco_unitario REAL NOT NULL,
                    taxas REAL DEFAULT 0.0,
                    custo_total REAL NOT NULL,
                    preco_medio REAL NOT NULL,
                    data_compra DATE NOT NULL,
                    quantidade_vendida INTEGER DEFAULT 0,
                    preco_venda REAL,
                    data_venda DATE,
                    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            print("✓ Tabela 'purchases' criada")
            
            # Criar índices
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON purchases(user_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_purchases_ticker ON purchases(ticker)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_purchases_data_compra ON purchases(data_compra)
            ''')
            print("✓ Índices criados para tabela 'purchases'")
        else:
            print("✓ Tabela 'purchases' já existe")
        
        # Verificar se a tabela price_history já existe
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='price_history'
        ''')
        
        if not cursor.fetchone():
            # Criar tabela de histórico de preços
            cursor.execute('''
                CREATE TABLE price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker VARCHAR(10) NOT NULL,
                    preco REAL NOT NULL,
                    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fonte VARCHAR(50) DEFAULT 'manual'
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_price_history_ticker ON price_history(ticker)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_price_history_data ON price_history(data_hora)
            ''')
            print("✓ Tabela 'price_history' criada")
        else:
            print("✓ Tabela 'price_history' já existe")
        
        conn.commit()
        print("\n✅ Novas tabelas adicionadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"✗ Erro ao adicionar tabelas: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def main():
    """Função principal"""
    print("=" * 50)
    print("INICIALIZAÇÃO DO BANCO DE DADOS - STONKS")
    print("=" * 50)
    
    # Verificar se já existem dados
    has_existing_data = check_existing_data()
    
    if has_existing_data:
        print("\n📊 Dados existentes encontrados. Adicionando novas tabelas sem perder dados...")
        
        # Adicionar apenas as novas tabelas
        if add_new_tables():
            print("\n✅ Sistema atualizado com sucesso!")
            print("\nPróximos passos:")
            print("1. Execute: pip install -r requirements.txt")
            print("2. Execute: python run.py")
            print("3. Acesse: http://localhost:5000")
            print("\nLogin administrador:")
            print("- Email: admin@stonks.com")
            print("- Senha: admin123")
        else:
            print("\n❌ Falha na atualização do banco de dados!")
    else:
        print("\n🆕 Criando banco de dados do zero...")
        
        # Criar todas as tabelas
        if create_tables():
            print("\n✅ Banco de dados inicializado com sucesso!")
            print("\nPróximos passos:")
            print("1. Execute: pip install -r requirements.txt")
            print("2. Execute: python run.py")
            print("3. Acesse: http://localhost:5000")
            print("\nLogin administrador:")
            print("- Email: admin@stonks.com")
            print("- Senha: admin123")
        else:
            print("\n❌ Falha na inicialização do banco de dados!")

if __name__ == '__main__':
    main()