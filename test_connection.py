#!/usr/bin/env python3
"""
Script para testar a conexão com o banco de dados e verificar o estado
"""

import sys
import os

# Adicionar diretório raiz ao path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from models.database import SessionLocal, test_connection
from models.stock import Stock
from models.user import User
from models.purchase import Purchase
from sqlalchemy import func

def main():
    print("=" * 60)
    print("TESTE DE CONEXÃO E ESTADO DO BANCO DE DADOS")
    print("=" * 60)
    
    # Testar conexão
    print("\n1. Testando conexão...")
    if test_connection():
        print("   ✅ Conexão com banco estabelecida com sucesso!")
    else:
        print("   ❌ Falha na conexão com o banco!")
        return
    
    # Verificar tabelas
    print("\n2. Verificando tabelas...")
    try:
        with SessionLocal() as db:
            # Contar registros em cada tabela
            users_count = db.query(User).count()
            stocks_count = db.query(Stock).count()
            purchases_count = db.query(Purchase).count()
            
            print(f"   - Users: {users_count} registros")
            print(f"   - Stocks: {stocks_count} registros")
            print(f"   - Purchases: {purchases_count} registros")
            
            if users_count > 0:
                print(f"   ✅ Banco contém dados!")
            else:
                print(f"   ⚠️  Banco está vazio de ações")
                
    except Exception as e:
        print(f"   ❌ Erro ao verificar tabelas: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verificar detalhes das ações se existirem
    if stocks_count > 0:
        print("\n3. Amostra de ações no banco:")
        try:
            with SessionLocal() as db:
                stocks = db.query(Stock).limit(5).all()
                for stock in stocks:
                    print(f"   - {stock.ticker}: {stock.empresa} (Score: {stock.score_final})")
        except Exception as e:
            print(f"   ❌ Erro ao listar ações: {e}")
    
    # Verificar usuário admin
    print("\n4. Verificando usuário administrador:")
    try:
        with SessionLocal() as db:
            admin = db.query(User).filter(User.email == 'admin@stonks.com').first()
            if admin:
                print(f"   ✅ Usuário admin encontrado: {admin.nome}")
                print(f"   - Email: {admin.email}")
                print(f"   - Ativo: {admin.ativo}")
                print(f"   - Email verificado: {admin.email_verificado}")
            else:
                print(f"   ❌ Usuário admin não encontrado!")
    except Exception as e:
        print(f"   ❌ Erro ao verificar admin: {e}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

if __name__ == '__main__':
    main()