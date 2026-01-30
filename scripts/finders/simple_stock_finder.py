#!/usr/bin/env python3
"""
Buscador Simplificado de Ações da B3
Versão sem unicode para compatibilidade
"""

import requests
import re
import random
import time
from typing import List, Dict
from config import Config

class SimpleStockFinder:
    """Buscador de ações da Bolsa Brasileira"""
    
    def __init__(self):
        self.cache = None
        self.cache_time = None
        self.cache_duration = 3600  # 1 hora
    
    def get_all_stocks(self) -> List[str]:
        """Obtém lista de todas as ações disponíveis"""
        # Verificar cache
        if (self.cache and self.cache_time and 
            (time.time() - self.cache_time) < self.cache_duration):
            print(f"Usando cache com {len(self.cache)} acoes")
            return self.cache
        
        print("Buscando lista de acoes via BrAPI...")
        
        try:
            url = "https://brapi.dev/api/available"
            params = {
                'token': Config.BRAPI_API_KEY,
                'search': 'stock'
            }
            
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('stocks'):
                    # Filtrar apenas tickers válidos
                    valid_tickers = []
                    pattern = r'^[A-Z]{4}[0-9]{1,2}$'
                    bdr_pattern = r'^[A-Z]{3,4}[0-9]{2}$'
                    
                    for stock in data['stocks']:
                        symbol = stock.get('symbol', '')
                        
                        # Verificar se é ticker válido
                        if (re.match(pattern, symbol) or re.match(bdr_pattern, symbol)):
                            valid_tickers.append(symbol)
                    
                    # Remover duplicatas e ordenar
                    valid_tickers = list(set(valid_tickers))
                    valid_tickers.sort()
                    
                    # Atualizar cache
                    self.cache = valid_tickers
                    self.cache_time = time.time()
                    
                    print(f"SUCESSO: {len(valid_tickers)} acoes encontradas")
                    return valid_tickers
                else:
                    print("Nenhuma acao encontrada")
                    return []
            else:
                print(f"ERRO HTTP: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"ERRO: {e}")
            return []
    
    def get_rotated_batch(self, batch_size: int = 20, exclude_recent: List[str] = None) -> List[str]:
        """Gera lote rotacionado de ações"""
        all_stocks = self.get_all_stocks()
        
        if not all_stocks:
            return []
        
        # Excluir recentes
        if exclude_recent:
            exclude_set = set(exclude_recent)
            available = [s for s in all_stocks if s not in exclude_set]
        else:
            available = all_stocks
        
        # Embaralhar
        random.shuffle(available)
        
        # Retornar lote
        batch = available[:batch_size]
        
        print(f"LOTE ROTACIONADO: {len(batch)} acoes")
        print(f"   Total disponivel: {len(available)}")
        
        return batch
    
    def get_top_liquidity_stocks(self, limit: int = 50) -> List[str]:
        """Retorna ações principais (top liquidez)"""
        # Lista hardcoded das principais ações por liquidez
        top_stocks = [
            'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
            'MGLU3', 'B3SA3', 'BRFS3', 'ABEV3', 'BPAC11',
            'ITSA4', 'SULA11', 'RAIL3', 'GGBR4', 'SUZB3',
            'CYRE3', 'EQTL3', 'RENT3', 'CVCB3', 'LREN3',
            'VIVT3', 'TIMS3', 'BBAS3', 'SANB11', 'CCRO3',
            'CSAN3', 'KLBN11', 'HYPE3', 'JBSS3', 'MRFG3',
            'COGN3', 'ENBR3', 'ELET3', 'RADL3', 'TOTS3',
            'YDUQ3', 'PRIO3', 'GOLL4', 'EMBR3', 'NTCO3',
            'PCAR3', 'CRFB3', 'IGTI11', 'SQIA3', 'SMFT3',
            'CIEL3', 'LWSA3', 'MDIA3', 'EZTC3', 'GRND3',
            'RRRP3', 'BIDI11', 'BOVA11', 'SMAL11', 'IVVB11'
        ]
        
        # Retornar apenas as disponíveis
        all_stocks = self.get_all_stocks()
        available_top = [s for s in top_stocks if s in all_stocks]
        
        return available_top[:limit]
    
    def get_random_sample(self, sample_size: int = 30) -> List[str]:
        """Retorna amostra aleatória de ações"""
        all_stocks = self.get_all_stocks()
        
        if not all_stocks:
            return []
        
        # Amostra aleatória
        sample = random.sample(all_stocks, min(sample_size, len(all_stocks)))
        
        print(f"AMOSTRA ALEATORIA: {len(sample)} acoes")
        return sample

def main():
    import sys
    
    finder = SimpleStockFinder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            print("LISTANDO ACOES DA B3")
            print("=" * 50)
            stocks = finder.get_all_stocks()
            
            print(f"Total encontrado: {len(stocks)} acoes")
            print("\nPrimeiras 20:")
            for i, ticker in enumerate(stocks[:20], 1):
                print(f"{i:2d}. {ticker}")
                
        elif command == "rotate":
            batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            print(f"GERANDO LOTE ROTACIONADO ({batch_size} acoes)")
            print("=" * 50)
            
            batch = finder.get_rotated_batch(batch_size)
            
            print(f"\nLote gerado:")
            for i, ticker in enumerate(batch, 1):
                print(f"{i:2d}. {ticker}")
                
        elif command == "top":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            print(f"TOP {limit} ACOES POR LIQUIDEZ")
            print("=" * 50)
            
            top_stocks = finder.get_top_liquidity_stocks(limit)
            
            print(f"\nTop {len(top_stocks)} acoes:")
            for i, ticker in enumerate(top_stocks, 1):
                print(f"{i:2d}. {ticker}")
                
        elif command == "random":
            sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            print(f"AMOSTRA ALEATORIA ({sample_size} acoes)")
            print("=" * 50)
            
            sample = finder.get_random_sample(sample_size)
            
            print(f"\nAmostra gerada:")
            for i, ticker in enumerate(sample, 1):
                print(f"{i:2d}. {ticker}")
        else:
            print("Comandos:")
            print("  python simple_stock_finder.py list")
            print("  python simple_stock_finder.py rotate [tamanho]")
            print("  python simple_stock_finder.py top [limite]")
            print("  python simple_stock_finder.py random [tamanho]")
    else:
        print("Uso: python simple_stock_finder.py [list|rotate|top|random]")

if __name__ == "__main__":
    main()