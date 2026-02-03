#!/usr/bin/env python3
"""
Script para inicializar o banco de dados PostgreSQL com ORM
"""

import sys
import os

# Adicionar diretório raiz ao path para importar models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from models.database import init_db, test_connection
from models.user import User
from models.stock import Stock
from models.purchase import Purchase
import bcrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Função principal"""
    print("=" * 50)
    print("INICIALIZACAO DO BANCO DE DADOS - POSTGRESQL")
    print("=" * 50)
    
    # Testar conexão
    if not test_connection():
        print("\nERRO: Nao foi possivel conectar ao PostgreSQL!")
        print("Verifique as credenciais no arquivo .env")
        return
    
    print(f"\n[OK] Conexao com PostgreSQL estabelecida com sucesso")
    
    # Criar tabelas
    print("\nCriando tabelas no banco de dados...")
    try:
        init_db()
        print("[OK] Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"[ERRO] Erro ao criar tabelas: {e}")
        return
    
    # Criar usuario administrador padrao
    print("\nCriando usuario administrador padrao...")
    try:
        from models.database import SessionLocal
        with SessionLocal() as db:
            # Verificar se admin ja existe
            existing_admin = db.query(User).filter(User.email == 'admin@stonks.com').first()
            
            if existing_admin:
                print("[AVISO] Usuario administrador ja existe")
            else:
                # Criar senha hash
                senha_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Criar usuario
                admin_user = User(
                    nome='Administrador',
                    email='admin@stonks.com',
                    senha_hash=senha_hash,
                    email_verificado=True,
                    ativo=True
                )
                
                db.add(admin_user)
                db.commit()
                
                print("[OK] Usuario administrador criado:")
                print(f"   Email: admin@stonks.com")
                print(f"   Senha: admin123")
                print("\n[IMPORTANTE] Altere a senha apos o primeiro login!")
                
    except Exception as e:
        print(f"[ERRO] Erro ao criar usuario administrador: {e}")
        logger.error(f"Erro ao criar admin: {e}", exc_info=True)
    
    print("\n" + "=" * 50)
    print("[OK] Banco de dados inicializado com sucesso!")
    print("=" * 50)

if __name__ == '__main__':
    main()