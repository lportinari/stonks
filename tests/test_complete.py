#!/usr/bin/env python3
"""
Teste completo da aplicação Stonks
"""

import requests
import json
import sys
import os

def test_api_endpoints():
    """Testa todos os endpoints da API"""
    
    base_url = "http://localhost:5000"
    
    print("Testando API do Stonks...")
    print(f"Base URL: {base_url}")
    print("=" * 50)
    
    # Testes a serem executados
    tests = [
        {
            'name': 'Página Principal',
            'url': '/',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Ranking',
            'url': '/api/ranking',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Top 5',
            'url': '/api/top?limit=5',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Setores',
            'url': '/api/sectors',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Estatísticas',
            'url': '/api/stats',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Pesos',
            'url': '/api/config/weights',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Busca VALE3',
            'url': '/api/stock/VALE3',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Comparação',
            'url': '/api/compare?tickers=VALE3,PETR4',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Filtros',
            'url': '/api/filter?min_dy=5&max_pl=15',
            'method': 'GET',
            'expected_status': 200
        },
        {
            'name': 'API Cache Info',
            'url': '/api/cache/info',
            'method': 'GET',
            'expected_status': 200
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n📋 Testando: {test['name']}")
            print(f"🔗 URL: {test['url']}")
            
            response = requests.get(f"{base_url}{test['url']}", timeout=10)
            
            if response.status_code == test['expected_status']:
                print(f"✅ Status: {response.status_code} (OK)")
                
                # Tentar parsear JSON se for API
                if test['url'].startswith('/api/'):
                    try:
                        data = response.json()
                        if data.get('success'):
                            print(f"📊 Resposta: SUCESSO")
                            if 'data' in data and isinstance(data['data'], list):
                                print(f"📈 Registros: {len(data['data'])}")
                            elif 'data' in data and isinstance(data['data'], dict):
                                print(f"📋 Dados: {list(data['data'].keys())[:5]}")
                        else:
                            print(f"⚠️ API retornou success=False")
                    except json.JSONDecodeError:
                        print(f"📄 Resposta não é JSON (conteúdo HTML)")
                
                passed += 1
            else:
                print(f"❌ Status: {response.status_code} (esperado: {test['expected_status']})")
                failed += 1
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de requisição: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADOS:")
    print(f"✅ Passaram: {passed}")
    print(f"❌ Falharam: {failed}")
    print(f"📈 Taxa de sucesso: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 Todos os testes passaram! Aplicação funcionando perfeitamente!")
        return True
    else:
        print(f"\n⚠️ {failed} teste(s) falharam. Verifique os logs.")
        return False

def test_database_connection():
    """Testa conexão com o banco de dados"""
    
    print("\n🗄️ Testando conexão com banco de dados...")
    
    try:
        from models.database import SessionLocal
        from models.stock import Stock
        
        session = SessionLocal()
        stock_count = session.query(Stock).count()
        session.close()
        
        print(f"✅ Conexão OK")
        print(f"📊 Total de ações no banco: {stock_count}")
        
        if stock_count > 0:
            return True
        else:
            print("⚠️ Nenhuma ação encontrada no banco")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def main():
    """Função principal"""
    
    print("STONKS - Teste Completo da Aplicacao")
    print("=" * 60)
    
    # Testar banco de dados
    db_ok = test_database_connection()
    
    if not db_ok:
        print("\n❌ Execute o script create_sample_data.py primeiro!")
        return False
    
    # Testar API
    api_ok = test_api_endpoints()
    
    print("\n" + "=" * 60)
    if db_ok and api_ok:
        print("🎉 APLICAÇÃO 100% FUNCIONAL!")
        print("🌐 Acesse: http://localhost:5000")
        print("📊 API Docs: http://localhost:5000/api/")
        return True
    else:
        print("❌ A aplicação precisa de correções")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)