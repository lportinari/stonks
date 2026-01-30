#!/usr/bin/env python3
"""
Teste simples do scraping do Fundamentus
"""

import requests
from bs4 import BeautifulSoup
import sys

def test_fundamentus_connection():
    """Testa conexão básica com Fundamentus"""
    
    print("Testando conexao com Fundamentus...")
    
    # URLs para teste
    urls = [
        'https://www.fundamentus.com.br/resultado.php',
        'https://www.fundamentus.com.br/index.php'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for url in urls:
        print(f"\nTestando URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"✅ Status Code: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Procurar tabelas
                tables = soup.find_all('table')
                print(f"📊 Tabelas encontradas: {len(tables)}")
                
                if tables:
                    # Analisar primeira tabela
                    first_table = tables[0]
                    rows = first_table.find_all('tr')
                    print(f"📏 Linhas na primeira tabela: {len(rows)}")
                    
                    if len(rows) > 1:
                        # Analisar cabeçalho
                        header_row = rows[0]
                        headers = header_row.find_all('th')
                        if headers:
                            header_texts = [h.get_text().strip() for h in headers]
                            print(f"📋 Cabeçalhos: {header_texts[:5]}...")  # Primeiros 5
                        
                        # Analisar primeira linha de dados
                        if len(rows) > 1:
                            data_row = rows[1]
                            cells = data_row.find_all(['td', 'th'])
                            if cells:
                                cell_texts = [cell.get_text().strip() for cell in cells]
                                print(f"📄 Primeira linha: {cell_texts[:5]}...")  # Primeiros 5
                    else:
                        print("⚠️ Tabela vazia ou sem dados")
                else:
                    print("⚠️ Nenhuma tabela encontrada")
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"❌ Erro de requisição: {e}")
        except Exception as e:
            print(f"❌ Erro geral: {e}")
    
    print("\n🏁 Teste concluído!")

if __name__ == "__main__":
    test_fundamentus_connection()