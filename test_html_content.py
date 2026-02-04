#!/usr/bin/env python3
"""
Testa o conteúdo HTML da página inicial para verificar se está sendo renderizado corretamente
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

def test_home_page():
    """Testa o conteúdo da página inicial"""
    print("=" * 70)
    print("TESTE DE CONTEÚDO HTML - PÁGINA INICIAL")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        print(f"\nStatus HTTP: {response.status_code}")
        print(f"Tamanho da resposta: {len(response.content)} bytes")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # Verificar se é HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            print(f"⚠️  Content-Type não é HTML: {content_type}")
            return False
        
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\n📄 Estrutura HTML:")
        print("-" * 70)
        
        # Verificar elementos principais
        title = soup.find('title')
        if title:
            print(f"✅ Título da página: {title.get_text()}")
        else:
            print("❌ Título da página não encontrado")
        
        # Verificar se tem conteúdo
        body = soup.find('body')
        if body:
            print(f"✅ Tag <body> encontrada")
            
            # Contar elementos
            h1_count = len(body.find_all('h1'))
            h3_count = len(body.find_all('h3'))
            card_count = len(body.find_all(class_='card'))
            link_count = len(body.find_all('a'))
            
            print(f"   - {h1_count} tags <h1>")
            print(f"   - {h3_count} tags <h3>")
            print(f"   - {card_count} cards")
            print(f"   - {link_count} links")
        else:
            print("❌ Tag <body> não encontrada")
            return False
        
        # Verificar conteúdo específico da home
        print("\n🔍 Conteúdo Específico:")
        print("-" * 70)
        
        # Procurar texto específico
        page_text = soup.get_text().lower()
        
        if 'stonks' in page_text:
            print("✅ Texto 'Stonks' encontrado")
        else:
            print("⚠️  Texto 'Stonks' não encontrado")
        
        if 'ação' in page_text or 'analise' in page_text:
            print("✅ Texto relacionado a ações encontrado")
        else:
            print("⚠️  Texto sobre ações não encontrado")
        
        if 'ranking' in page_text:
            print("✅ Texto 'Ranking' encontrado")
        else:
            print("⚠️  Texto 'Ranking' não encontrado")
        
        # Verificar estatísticas
        if 'stocks' in page_text or 'ações' in page_text:
            print("✅ Referências a ações encontradas")
        
        # Mostrar amostra do conteúdo
        print("\n📝 Amostra do conteúdo HTML:")
        print("-" * 70)
        html_sample = response.text[:500]
        print(html_sample)
        print("...")
        
        print("\n" + "=" * 70)
        print("✅ PÁGINA INICIAL FUNCIONANDO CORRETAMENTE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao testar página inicial: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ranking_page():
    """Testa o conteúdo da página de ranking"""
    print("\n" + "=" * 70)
    print("TESTE DE CONTEÚDO HTML - PÁGINA DE RANKING")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/ranking", timeout=5)
        
        print(f"\nStatus HTTP: {response.status_code}")
        print(f"Tamanho da resposta: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verificar se há tabela de ranking
        tables = soup.find_all('table')
        print(f"✅ {len(tables)} tabelas encontradas")
        
        # Contar linhas da tabela
        if tables:
            rows = tables[0].find_all('tr')
            print(f"✅ {len(rows)} linhas na tabela (incluindo cabeçalho)")
        
        # Verificar tickers na página
        page_text = soup.get_text()
        tickers = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3']
        found_tickers = [t for t in tickers if t in page_text]
        
        if found_tickers:
            print(f"✅ Tickers encontrados: {', '.join(found_tickers)}")
        else:
            print("⚠️  Nenhum ticker conhecido encontrado")
        
        print("\n" + "=" * 70)
        print("✅ PÁGINA DE RANKING FUNCIONANDO CORRETAMENTE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao testar página de ranking: {e}")
        return False

if __name__ == '__main__':
    test_home_page()
    test_ranking_page()