#!/usr/bin/env python3
"""
Script para testar as rotas da aplicação enquanto ela está rodando
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_route(route, description=""):
    """Testa uma rota específica"""
    try:
        response = requests.get(f"{BASE_URL}{route}", timeout=5)
        status_icon = "✅" if response.status_code == 200 else "⚠️ "
        print(f"{status_icon} {route} - Status: {response.status_code}")
        if description:
            print(f"   ({description})")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {route} - Erro: {str(e)}")
        return False

def test_api_route(route, description=""):
    """Testa uma rota da API"""
    try:
        response = requests.get(f"{BASE_URL}{route}", timeout=5)
        status_icon = "✅" if response.status_code == 200 else "⚠️ "
        print(f"{status_icon} {route} - Status: {response.status_code}")
        if description:
            print(f"   ({description})")
        if response.status_code == 200:
            try:
                data = response.json()
                if 'success' in data and data['success']:
                    print(f"   ✓ Resposta: {json.dumps(data, indent=2)[:200]}...")
                else:
                    print(f"   Resposta: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   Resposta não é JSON")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {route} - Erro: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("TESTE DE ROTAS DA APLICAÇÃO STONKS")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 70)
    
    success_count = 0
    total_count = 0
    
    # Rotas principais
    print("\n📄 ROTAS PRINCIPAIS:")
    print("-" * 70)
    routes = [
        ("/", "Página inicial"),
        ("/ranking", "Ranking de ações"),
        ("/simulador", "Simulador de juros"),
    ]
    
    for route, desc in routes:
        total_count += 1
        if test_route(route, desc):
            success_count += 1
        print()
    
    # Rotas de API
    print("\n🔧 ROTAS DE API:")
    print("-" * 70)
    api_routes = [
        ("/api/stocks/search?ticker=PETR4", "Buscar ação PETR4"),
        ("/api/stocks/suggestions?q=VALE", "Sugestões VALE"),
        ("/api/stocks/PETR4", "Detalhes PETR4"),
        ("/api/market/summary", "Resumo do mercado"),
    ]
    
    for route, desc in api_routes:
        total_count += 1
        if test_api_route(route, desc):
            success_count += 1
        print()
    
    # Rotas de autenticação
    print("\n🔐 ROTAS DE AUTENTICAÇÃO:")
    print("-" * 70)
    auth_routes = [
        ("/auth/login", "Página de login"),
        ("/auth/register", "Página de registro"),
    ]
    
    for route, desc in auth_routes:
        total_count += 1
        if test_route(route, desc):
            success_count += 1
        print()
    
    # Rotas de compras
    print("\n💰 ROTAS DE COMPRAS:")
    print("-" * 70)
    purchase_routes = [
        ("/purchases", "Dashboard de compras"),
    ]
    
    for route, desc in purchase_routes:
        total_count += 1
        if test_route(route, desc):
            success_count += 1
        print()
    
    # Resumo
    print("=" * 70)
    print(f"RESULTADO: {success_count}/{total_count} rotas testadas com sucesso")
    print(f"Taxa de sucesso: {(success_count/total_count*100):.1f}%")
    print("=" * 70)
    
    if success_count == total_count:
        print("✅ TODAS AS ROTAS ESTÃO FUNCIONANDO!")
    elif success_count > total_count * 0.8:
        print("⚠️  MAIORIA DAS ROTAS FUNCIONANDO")
    else:
        print("❌ PROBLEMAS DETECTADOS NAS ROTAS")

if __name__ == '__main__':
    main()