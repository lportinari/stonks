import requests
import json

# Configurações do Teste
BASE_URL = "http://127.0.0.1:5000"
# Nota: Como criamos um novo Blueprint 'api_v2', precisamos ajustar a URL das rotas corrigidas.
# Se você registrou o api_v2_bp como '/api', use as URLs abaixo. 
# Se precisar ajustar no app.py para '/api', assumiremos que as rotas estão acessíveis via '/api/v2' 
# ou que você substituirá o arquivo antigo. 
# Para fins de teste, vamos assumir que as rotas corrigidas estão disponíveis.

API_BASE = f"{BASE_URL}/api" 

# Lista de Testes
tests = [
    {"name": "Listar Ações (Fix 404)", "method": "GET", "url": f"{API_BASE}/stocks", "expected_status": 200},
    {"name": "Detalhes PETR4 (Fix 500)", "method": "GET", "url": f"{API_BASE}/stocks/PETR4", "expected_status": 200},
    {"name": "Detalhes VALE3", "method": "GET", "url": f"{API_BASE}/stocks/VALE3", "expected_status": 200},
    {"name": "Resumo de Mercado (Fix 500)", "method": "GET", "url": f"{API_BASE}/market/summary", "expected_status": 200},
    {"name": "Estatísticas Gerais (Fix 404)", "method": "GET", "url": f"{API_BASE}/stats", "expected_status": 200},
    {"name": "Ranking de Usuários (Fix 404)", "method": "GET", "url": f"{API_BASE}/ranking", "expected_status": 200},
    {"name": "Filtro de Ações (Fix 500)", "method": "GET", "url": f"{BASE_URL}/filter?min_price=15.0", "expected_status": 200},
]

def run_tests():
    print("\n" + "="*50)
    print(f" INICIANDO TESTES DE API EM {BASE_URL}")
    print("="*50)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            response = requests.request(test['method'], test['url'])
            
            status = "PASS" if response.status_code == test['expected_status'] else "FAIL"
            
            if status == "PASS":
                passed += 1
                print(f"\n[OK] {test['name']}")
                print(f"    Status: {response.status_code}")
                print(f"    Resposta: {response.json()}")
            else:
                failed += 1
                print(f"\n[FALHOU] {test['name']}")
                print(f"    Esperado: {test['expected_status']}, Recebido: {response.status_code}")
                print(f"    Resposta: {response.text}")
                
        except Exception as e:
            failed += 1
            print(f"\n[ERRO] {test['name']}")
            print(f"    Exceção: {e}")
            
    print("\n" + "="*50)
    print(" RESUMO DOS TESTES")
    print("="*50)
    print(f"Total: {len(tests)} | Passou: {passed} | Falhou: {failed}")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_tests()