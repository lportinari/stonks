#!/usr/bin/env python3
"""
Script de teste detalhado das rotas da aplicação
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
import json

def test_route(client, method, path, data=None, description=""):
    """Testa uma rota específica"""
    try:
        if method == 'GET':
            response = client.get(path)
        elif method == 'POST':
            response = client.post(path, json=data or {})
        else:
            return False, f"Método {method} não suportado"
        
        status = response.status_code
        success = status < 400
        
        # Tentar pegar JSON da resposta
        try:
            content = response.get_json()
        except:
            content = f"{len(response.data)} bytes"
        
        print(f"{'[OK]' if success else '[FAIL]'} {method:6} {path:40} - Status: {status:3} - {description}")
        if not success and status != 404:
            print(f"   Erro: {content}")
        
        return success, None
    except Exception as e:
        print(f"[ERROR] {method:6} {path:40} - ERRO: {str(e)}")
        return False, str(e)

def main():
    """Função principal"""
    print("=" * 70)
    print("TESTE DETALHADO DAS ROTAS - STONKS")
    print("=" * 70)
    
    # Criar aplicação
    print("\n[1] Criando aplicacao Flask...")
    try:
        app = create_app()
        print("[OK] Aplicacao criada com sucesso")
    except Exception as e:
        print(f"[ERRO] Erro ao criar aplicacao: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Criar cliente de teste
    print("\n[2] Criando cliente de teste...")
    client = app.test_client()
    print("[OK] Cliente de teste criado")
    
    # Listar todas as rotas
    print("\n[3] Listando todas as rotas registradas...")
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'rule': rule.rule,
            'methods': list(rule.methods),
            'endpoint': rule.endpoint
        })
    
    print(f"[OK] Encontradas {len(routes)} rotas")
    
    # Testar rotas principais
    print("\n[4] Testando rotas principais...")
    print("-" * 70)
    
    tests = [
        # Rotas principais
        ('GET', '/', 'Pagina inicial'),
        ('GET', '/ranking', 'Pagina de ranking'),
        ('GET', '/simulador', 'Simulador de juros compostos'),
        
        # Rotas de API
        ('GET', '/api/stocks/search?ticker=VALE3', 'Busca de acao'),
        ('GET', '/api/stocks/suggestions?q=VALE', 'Sugestoes de autocomplete'),
        ('GET', '/api/stocks/VALE3', 'Detalhes da acao VALE3'),
        ('GET', '/api/market/summary', 'Resumo do mercado'),
        
        # Rotas de autenticacao
        ('GET', '/auth/login', 'Pagina de login'),
        ('GET', '/auth/register', 'Pagina de registro'),
        ('GET', '/auth/profile', 'Perfil do usuario (deve falhar sem login)'),
        
        # Rotas de compras
        ('GET', '/purchases', 'Pagina de compras (deve falhar sem login)'),
        ('GET', '/purchases/dashboard', 'Dashboard de portfolio (deve falhar sem login)'),
    ]
    
    results = {'success': 0, 'fail': 0, 'error': 0}
    
    for method, path, description in tests:
        success, error = test_route(client, method, path, description=description)
        if success:
            results['success'] += 1
        elif error:
            results['error'] += 1
        else:
            results['fail'] += 1
    
    # Resumo dos testes
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    print(f"[OK] Sucesso: {results['success']}")
    print(f"[FAIL] Falha:   {results['fail']}")
    print(f"[ERRO] Erro:    {results['error']}")
    print(f"Total:          {results['success'] + results['fail'] + results['error']}")
    
    # Teste de conexao com banco
    print("\n[5] Testando conexao com banco de dados...")
    try:
        from models.database import test_connection, SessionLocal
        from config import Config
        
        print(f"Tipo de banco: {Config.get_db_type()}")
        print(f"URL: {Config.DATABASE_URL[:50]}..." if Config.DATABASE_URL else "Nao configurada")
        
        if test_connection():
            print("[OK] Conexao com banco estabelecida")
            
            # Testar query simples
            with SessionLocal() as db:
                from models.user import User
                count = db.query(User).count()
                print(f"[OK] Query executada: {count} usuarios no banco")
        else:
            print("[ERRO] Falha na conexao com banco")
    except Exception as e:
        print(f"[ERRO] Erro ao testar conexao: {e}")
        import traceback
        traceback.print_exc()
    
    # Verificar modelos
    print("\n[6] Verificando modelos...")
    try:
        from models.user import User
        from models.stock import Stock
        from models.purchase import Purchase
        
        print("[OK] Modelo User importado")
        print("[OK] Modelo Stock importado")
        print("[OK] Modelo Purchase importado")
    except Exception as e:
        print(f"[ERRO] Erro ao importar modelos: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("TESTES CONCLUIDOS")
    print("=" * 70)

if __name__ == '__main__':
    main()