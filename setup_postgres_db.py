#!/usr/bin/env python3
"""
Script para verificar e criar banco de dados PostgreSQL
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("VERIFICAÇÃO E CRIAÇÃO DO BANCO DE DADOS")
print("=" * 60)

# Configurações do .env
pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
pg_port = int(os.environ.get('POSTGRES_PORT', '5432'))
pg_db = os.environ.get('POSTGRES_DB', 'stonks')
pg_user = os.environ.get('POSTGRES_USER', 'postgres')
pg_password = os.environ.get('POSTGRES_PASSWORD', 'postgres')

print(f"\nConfigurações:")
print(f"  Host: {pg_host}")
print(f"  Port: {pg_port}")
print(f"  Database: {pg_db}")
print(f"  User: {pg_user}")

try:
    # Conectar ao PostgreSQL (banco postgres padrão)
    print(f"\nConectando ao PostgreSQL...")
    conn = psycopg2.connect(
        host=pg_host,
        port=pg_port,
        database='postgres',  # Conectar ao banco padrão
        user=pg_user,
        password=pg_password,
        connect_timeout=5
    )
    conn.autocommit = True  # Necessário para CREATE DATABASE
    print("✅ Conexão estabelecida!")
    
    cursor = conn.cursor()
    
    # Verificar se o banco já existe
    cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = {}").format(
        sql.Literal(pg_db)
    ))
    exists = cursor.fetchone()
    
    if exists:
        print(f"\n✅ O banco de dados '{pg_db}' já existe!")
        
        # Listar tabelas existentes
        cursor.execute(sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        tables = cursor.fetchall()
        
        if tables:
            print(f"\nTabelas encontradas:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print(f"\n⚠️  Banco de dados '{pg_db}' existe mas não possui tabelas")
    else:
        print(f"\n⚠️  O banco de dados '{pg_db}' NÃO existe!")
        print(f"   Criando banco de dados '{pg_db}'...")
        
        try:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(pg_db)
            ))
            print(f"✅ Banco de dados '{pg_db}' criado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar banco de dados: {e}")
            cursor.close()
            conn.close()
            exit(1)
    
    cursor.close()
    conn.close()
    print("\n✅ Conexão encerrada")
    
    # Testar conexão com o banco específico
    print(f"\nTestando conexão com o banco '{pg_db}'...")
    try:
        conn2 = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_db,
            user=pg_user,
            password=pg_password,
            connect_timeout=5
        )
        print("✅ Conexão com banco '{}' estabelecida!".format(pg_db))
        conn2.close()
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco '{pg_db}': {e}")
        exit(1)
    
    print("\n" + "=" * 60)
    print("Próximo passo: Execute o script de inicialização:")
    print("  python scripts/init_postgres_db.py")
    print("=" * 60)
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Erro de conexão:")
    print(f"   {e}")
    print(f"\nPossíveis causas:")
    print(f"   1. Senha do usuário postgres incorreta")
    print(f"   2. PostgreSQL não aceita conexões TCP/IP")
    print(f"   3. Firewall bloqueando conexões")
    print(f"\nSoluções:")
    print(f"   - Verifique se pg_hba.conf permite conexões:")
    print(f"     host    all             all             127.0.0.1/32            md5")
    print(f"   - Reinicie o PostgreSQL após alterar configurações")
    
except ImportError as e:
    print(f"\n❌ Erro: psycopg2 não está instalado")
    print(f"   Instale com: pip install psycopg2-binary")
    
except Exception as e:
    print(f"\n❌ Erro inesperado:")
    print(f"   {type(e).__name__}: {e}")