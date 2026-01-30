#!/usr/bin/env python3
import requests
import json
import sys

def test_api():
    base_url = "http://localhost:5000"
    
    print("Testando API Stonks...")
    print("=" * 40)
    
    endpoints = [
        ("/", "Pagina Principal"),
        ("/api/ranking", "API Ranking"),
        ("/api/top?limit=5", "API Top 5"),
        ("/api/stock/VALE3", "API VALE3"),
        ("/api/sectors", "API Setores")
    ]
    
    passed = 0
    failed = 0
    
    for url, name in endpoints:
        try:
            response = requests.get(f"{base_url}{url}", timeout=5)
            
            if response.status_code == 200:
                print(f"[OK] {name}: {response.status_code}")
                passed += 1
            else:
                print(f"[FAIL] {name}: {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            failed += 1
    
    print("=" * 40)
    print(f"Resultados: {passed} OK, {failed} FAIL")
    
    if failed == 0:
        print("\nAplicacao funcionando perfeitamente!")
        print(f"Acesse: {base_url}")
        return True
    else:
        print(f"\n{failed} testes falharam")
        return False

if __name__ == "__main__":
    test_api()