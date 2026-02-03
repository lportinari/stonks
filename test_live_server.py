#!/usr/bin/env python3
"""
Script para testar a aplicação em um servidor Flask real
"""

import sys
import os
import time
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def test_url(url, description=""):
    """Testa uma URL"""
    try:
        response = requests.get(url, timeout=5)
        status = response.status_code
        content = response.text
        
        # Verificar se o HTML é válido
        has_html = '<!DOCTYPE html>' in content or '<html' in content
        has_body = '<body' in content or '</body>' in content
        has_content = len(content) > 100
        
        # Verificar conteúdo específico
        if "inicial" in description.lower():
            has_specific = 'Stonks' in content or 'Análise' in content
        elif "ranking" in description.lower():
            has_specific = 'Ranking' in content
        elif "login" in description.lower():
            has_specific = 'Login' in content or 'Senha' in content
        elif "api" in description.lower():
            has_specific = True  # API retorna JSON
        else:
            has_specific = True
        
        success = (status == 200 or status == 302 or status == 308) and (has_html or "api" in description.lower()) and has_content and has_specific
        
        print(f"{'[OK]' if success else '[FAIL]'} {url:50} - Status: {status:3} - {description}")
        if not success:
            print(f"   Conteúdo: {content[:200]}")
        
        return success
    except Exception as e:
        print(f"[ERROR] {url:50} - ERRO: {str(e)}")
        return False

def main():
    """Função principal"""
    print("=" * 70)
    print("TESTE DA APLICAÇÃO EM SERVIDOR REAL")
    print("=" * 70)
    
    # Criar aplicação
    print("\n[1] Criando aplicação Flask...")
    app = create_app()
    print("[OK] Aplicação criada com sucesso")
    
    # Iniciar servidor em thread separada
    print("\n[2] Iniciando servidor Flask...")
    import threading
    
    def run_server():
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Esperar servidor iniciar
    print("[INFO] Aguardando servidor iniciar...")
    time.sleep(3)
    
    # Testar URLs
    print("\n[3] Testando URLs...")
    print("-" * 70)
    
    base_url = "http://127.0.0.1:5000"
    
    tests = [
        (f"{base_url}/", 'Pagina inicial'),
        (f"{base_url}/ranking", 'Pagina de ranking'),
        (f"{base_url}/simulador", 'Simulador'),
        (f"{base_url}/auth/login", 'Pagina de login'),
        (f"{base_url}/auth/register", 'Pagina de registro'),
        (f"{base_url}/api/market/summary", 'API Resumo do mercado'),
        (f"{base_url}/api/stocks/search?ticker=VALE3", 'API Busca acao'),
    ]
    
    results = {'success': 0, 'fail': 0}
    
    for url, description in tests:
        success = test_url(url, description=description)
        if success:
            results['success'] += 1
        else:
            results['fail'] += 1
    
    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    print(f"[OK] Sucesso: {results['success']}")
    print(f"[FAIL] Falha:   {results['fail']}")
    print(f"Total:          {results['success'] + results['fail']}")
    
    print("\n" + "=" * 70)
    print(f"Servidor rodando em {base_url}")
    print("Pressione Ctrl+C para parar o servidor")
    print("=" * 70)
    
    # Manter servidor rodando
    try:
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Encerrando servidor...")

if __name__ == '__main__':
    main()