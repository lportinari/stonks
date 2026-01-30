#!/usr/bin/env python3
"""
Diagnóstico de problemas na aplicação
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnose_imports():
    """Diagnostica problemas de importação"""
    print("=== DIAGNÓSTICO DE IMPORTAÇÕES ===")
    
    try:
        from models.database import SessionLocal, init_db
        print("✅ models.database OK")
    except Exception as e:
        print(f"❌ models.database: {e}")
        return False
    
    try:
        from models.stock import Stock
        print("✅ models.stock OK")
    except Exception as e:
        print(f"❌ models.stock: {e}")
        return False
    
    try:
        from services.ranking_service import RankingService
        print("✅ services.ranking_service OK")
    except Exception as e:
        print(f"❌ services.ranking_service: {e}")
        return False
    
    try:
        from routes.main import main_bp
        print("✅ routes.main OK")
    except Exception as e:
        print(f"❌ routes.main: {e}")
        return False
    
    try:
        from routes.api import api_bp
        print("✅ routes.api OK")
    except Exception as e:
        print(f"❌ routes.api: {e}")
        return False
    
    try:
        from flask import Flask
        print("✅ Flask OK")
    except Exception as e:
        print(f"❌ Flask: {e}")
        return False
    
    return True

def diagnose_routes():
    """Diagnostica problemas nas rotas"""
    print("\n=== DIAGNÓSTICO DE ROTAS ===")
    
    try:
        from app import create_app
        app = create_app()
        
        print("✅ App criado com sucesso")
        
        # Listar todas as rotas
        print("\nRotas registradas:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar app: {e}")
        import traceback
        traceback.print_exc()
        return False

def diagnose_database():
    """Diagnostica problemas no banco"""
    print("\n=== DIAGNÓSTICO DE BANCO ===")
    
    try:
        from models.database import SessionLocal
        from models.stock import Stock
        
        session = SessionLocal()
        count = session.query(Stock).count()
        session.close()
        
        print(f"✅ Conexão OK - {count} ações no banco")
        return True
        
    except Exception as e:
        print(f"❌ Erro no banco: {e}")
        return False

def main():
    """Função principal"""
    print("STONKS - DIAGNÓSTICO COMPLETO")
    print("=" * 50)
    
    # Testar importações
    imports_ok = diagnose_imports()
    
    if not imports_ok:
        print("\n❌ Problemas críticos nas importações!")
        return False
    
    # Testar rotas
    routes_ok = diagnose_routes()
    
    # Testar banco
    db_ok = diagnose_database()
    
    print("\n" + "=" * 50)
    if imports_ok and routes_ok and db_ok:
        print("✅ Todos os componentes funcionando!")
        return True
    else:
        print("❌ Problemas encontrados!")
        return False

if __name__ == "__main__":
    main()