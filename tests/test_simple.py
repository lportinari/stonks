#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def test_connection():
    print("Testando conexao com Fundamentus...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get('https://www.fundamentus.com.br/resultado.php', headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table')
            print(f"Tabelas encontradas: {len(tables)}")
            
            if tables:
                first_table = tables[0]
                rows = first_table.find_all('tr')
                print(f"Linhas na primeira tabela: {len(rows)}")
                
                if len(rows) > 1:
                    print("Sucesso! Estrutura da pagina detectada.")
                    return True
        else:
            print("Erro ao acessar site")
            
    except Exception as e:
        print(f"Erro: {e}")
    
    return False

if __name__ == "__main__":
    test_connection()