#!/usr/bin/env python3
"""
Script de teste detalhado das rotas com verificação de conteúdo HTML
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def test_page_content(client, path, description=""):
    """Testa uma página e verifica o conteúdo"""
    try:
        response = client.get(path, follow_redirects=True)
        status = response.status_code
        content = response.data.decode('utf-8', errors='ignore')
        
        # Verificar se o HTML é válido
        has_html = '<!DOCTYPE html>' in content or '<html' in content
        has_body = '<body' in content or '</body>' in content
        has_content = len(content) > 100
        
        # Verificar se há erros de template
        has_error = 'TemplateNotFound' in content or 'TemplateError' in content or 'Jinja2' in content
        
        # Verificar se há traceback de erro
        has_traceback = 'Traceback' in content or 'File "' in content
        
        # Verificar conteúdo específico
        if description == "Pagina inicial":
            has_specific_content = 'Stonks' in content or 'Análise de Ações' in content
        elif description == "Pagina de ranking":
            has_specific_content = 'Ranking' in content or 'Tabela' in content
        elif description == "Pagina de login":
            has_specific_content = 'Login' in content or 'Senha' in content
        else:
            has_specific_content = True
        
        # Resultado
        success = (status == 200 or status == 302 or status == 308) and has_html and has_body and has_content and not has_error and not has_traceback and has_specific_content
        
        print(f"{'[OK]' if success else '[FAIL]'} {path:40} - Status: {status:3} - {description}")
        print(f"   HTML válido: {has_html}, Tem body: {has_body}, Tamanho: {len(content)} bytes")
        print(f"   Conteúdo específico: {has_specific_content}, Erro: {has_error or has_traceback}")
        
        if not success:
            print(f"   Primeiros 500 caracteres:\n{content[:500]}")
        
        return success, content if success else None
        
    except Exception as e:
        print(f"[ERROR] {path:40} - ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Função principal"""
    print("=" * 70)
    print("TESTE DETALHADO DO CONTEÚDO DAS PÁGINAS")
    print("=" * 70)
    
    # Criar aplicação
    print("\n[1] Criando aplicação Flask...")
    try:
        app = create_app()
        print("[OK] Aplicação criada com sucesso")
    except Exception as e:
        print(f"[ERRO] Erro ao criar aplicação: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Criar cliente de teste
    print("\n[2] Criando cliente de teste...")
    client = app.test_client()
    print("[OK] Cliente de teste criado")
    
    # Testar páginas principais
    print("\n[3] Testando páginas principais com verificação de conteúdo...")
    print("-" * 70)
    
    tests = [
        ('/', 'Pagina inicial'),
        ('/ranking', 'Pagina de ranking'),
        ('/simulador', 'Simulador de juros compostos'),
        ('/auth/login', 'Pagina de login'),
        ('/auth/register', 'Pagina de registro'),
        ('/api/market/summary', 'Resumo do mercado (API)'),
        ('/api/stocks/search?ticker=VALE3', 'Busca de ação (API)'),
    ]
    
    results = {'success': 0, 'fail': 0, 'content': {}}
    
    for path, description in tests:
        success, content = test_page_content(client, path, description=description)
        if success and content:
            results['success'] += 1
            results['content'][path] = content
        else:
            results['fail'] += 1
    
    # Resumo dos testes
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    print(f"[OK] Sucesso: {results['success']}")
    print(f"[FAIL] Falha:   {results['fail']}")
    print(f"Total:          {results['success'] + results['fail']}")
    
    # Exibir conteúdo da home para debug
    if '/' in results['content']:
        print("\n" + "=" * 70)
        print("CONTEÚDO DA PÁGINA INICIAL (primeiros 1000 caracteres)")
        print("=" * 70)
        print(results['content']['/'][:1000])
    
    print("\n" + "=" * 70)
    print("TESTES CONCLUÍDOS")
    print("=" * 70)

if __name__ == '__main__':
    main()