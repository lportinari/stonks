#!/usr/bin/env python3
"""
Buscador de Ações da B3
Obtém lista completa de ações e implementa rotação dinâmica
"""

import requests
import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re
from config import Config

logger = logging.getLogger(__name__)

class B3StockFinder:
    """Buscador de ações da Bolsa Brasileira"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        }
        
        # Cache de ações encontradas
        self.all_stocks_cache = None
        self.cache_timestamp = None
        self.cache_duration = 3600  # 1 hora
    
    def get_b3_stocks_from_brapi(self) -> List[Dict]:
        """
        Obtém lista completa de ações disponíveis na B3 via BrAPI
        """
        try:
            print("Buscando lista completa de ações via BrAPI...")
            
            # Endpoint de listagem de ações
            url = "https://brapi.dev/api/available"
            params = {
                'token': Config.BRAPI_API_KEY,
                'search': 'stock'  # Apenas ações
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('stocks'):
                    stocks = []
                    
                    for stock in data['stocks']:
                        # Filtrar apenas ações comuns (3, 4, 5, 6, 11)
                        symbol = stock.get('symbol', '')
                        
                        # Verificar se é ticker válido de ação
                        if self._is_valid_stock_ticker(symbol):
                            stocks.append({
                                'ticker': symbol,
                                'name': stock.get('name', ''),
                                'sector': stock.get('sector', ''),
                                'industry': stock.get('industry', ''),
                                'market_cap': stock.get('marketCap'),
                                'currency': stock.get('currency', 'BRL')
                            })
                    
                    print(f"✅ Encontradas {len(stocks)} ações válidas na B3")
                    return stocks
                else:
                    print("❌ Nenhuma ação encontrada na resposta")
                    return []
            else:
                print(f"❌ Erro HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao buscar ações via BrAPI: {e}")
            return []
    
    def get_b3_stocks_from_fundamentus(self) -> List[Dict]:
        """
        Obtém lista de ações via scraping do Fundamentus (fallback)
        """
        try:
            print("Buscando ações via Fundamentus (fallback)...")
            
            url = "https://www.fundamentus.com.br/resultado.php"
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                stocks = []
                table = soup.find('table')
                
                if table:
                    rows = table.find_all('tr')[1:]  # Pular header
                    
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            ticker = cols[0].text.strip()
                            name = cols[1].text.strip()
                            
                            if self._is_valid_stock_ticker(ticker):
                                stocks.append({
                                    'ticker': ticker,
                                    'name': name,
                                    'sector': '',
                                    'industry': '',
                                    'market_cap': None,
                                    'currency': 'BRL'
                                })
                
                print(f"✅ Encontradas {len(stocks)} ações via Fundamentus")
                return stocks
            else:
                print(f"❌ Erro HTTP {response.status_code} no Fundamentus")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao buscar ações via Fundamentus: {e}")
            return []
    
    def get_b3_stocks_from_yahoo(self) -> List[Dict]:
        """
        Obtém lista de ações via Yahoo Finance (fallback)
        """
        try:
            print("Buscando ações via Yahoo Finance (fallback)...")
            
            # Usar índice Bovespa para obter componentes
            url = "https://query1.finance.yahoo.com/v1/finance/lookup"
            params = {
                'start': 0,
                'count': 250,  # Limite máximo
                'q': '^BVSP'  # Índice Bovespa
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                stocks = []
                
                if 'finance' in data and 'result' in data['finance']:
                    for item in data['finance']['result'][0]['quotes']:
                        symbol = item.get('symbol', '')
                        
                        # Filtrar apenas ações brasileiras
                        if symbol.endswith('.SA') and self._is_valid_stock_ticker(symbol.replace('.SA', '')):
                            stocks.append({
                                'ticker': symbol.replace('.SA', ''),
                                'name': item.get('longname', ''),
                                'sector': '',
                                'industry': '',
                                'market_cap': None,
                                'currency': 'BRL'
                            })
                
                print(f"✅ Encontradas {len(stocks)} ações via Yahoo Finance")
                return stocks
            else:
                print(f"❌ Erro HTTP {response.status_code} no Yahoo")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao buscar ações via Yahoo: {e}")
            return []
    
    def _is_valid_stock_ticker(self, ticker: str) -> bool:
        """
        Verifica se o ticker é uma ação válida da B3
        """
        if not ticker or len(ticker) < 4 or len(ticker) > 7:
            return False
        
        # Padrões válidos de tickers brasileiros
        pattern = r'^[A-Z]{4}[0-9]{1,2}$'
        
        # Permitir também tickers como BDR11, etc.
        bdr_pattern = r'^[A-Z]{3,4}[0-9]{2}$'
        
        return (re.match(pattern, ticker) is not None or 
                re.match(bdr_pattern, ticker) is not None)
    
    def get_all_b3_stocks(self, use_cache: bool = True) -> List[Dict]:
        """
        Obtém lista completa de ações da B3 com cache
        """
        # Verificar cache
        if (use_cache and 
            self.all_stocks_cache and 
            self.cache_timestamp and 
            (time.time() - self.cache_timestamp) < self.cache_duration):
            print(f"Usando cache com {len(self.all_stocks_cache)} ações")
            return self.all_stocks_cache
        
        print("Atualizando cache de ações da B3...")
        
        # Tentar fontes em ordem de preferência
        all_stocks = []
        
        # 1. BrAPI (mais completa)
        stocks = self.get_b3_stocks_from_brapi()
        if stocks:
            all_stocks.extend(stocks)
        
        # 2. Fundamentus (fallback)
        if len(all_stocks) < 100:  # Se encontrou poucas, tentar outra fonte
            stocks = self.get_b3_stocks_from_fundamentus()
            if stocks:
                all_stocks.extend(stocks)
        
        # 3. Yahoo Finance (último fallback)
        if len(all_stocks) < 50:
            stocks = self.get_b3_stocks_from_yahoo()
            if stocks:
                all_stocks.extend(stocks)
        
        # Remover duplicatas
        unique_stocks = []
        seen_tickers = set()
        
        for stock in all_stocks:
            ticker = stock['ticker']
            if ticker not in seen_tickers:
                seen_tickers.add(ticker)
                unique_stocks.append(stock)
        
        # Atualizar cache
        self.all_stocks_cache = unique_stocks
        self.cache_timestamp = time.time()
        
        print(f"✅ Total de {len(unique_stocks)} ações únicas encontradas")
        return unique_stocks
    
    def get_rotated_stocks(self, batch_size: int = 20, exclude_recent: List[str] = None) -> List[str]:
        """
        Obtém lote rotacionado de ações para atualização
        """
        all_stocks = self.get_all_b3_stocks()
        
        if not all_stocks:
            print("❌ Nenhuma ação encontrada para rotação")
            return []
        
        # Extrair apenas tickers
        all_tickers = [stock['ticker'] for stock in all_stocks]
        
        # Excluir recentes se solicitado
        if exclude_recent:
            exclude_set = set(exclude_recent)
            all_tickers = [t for t in all_tickers if t not in exclude_set]
        
        # Embaralhar para rotação
        import random
        random.shuffle(all_tickers)
        
        # Retornar lote solicitado
        batch = all_tickers[:batch_size]
        
        print(f"🔄 Gerado lote rotacionado de {len(batch)} ações")
        print(f"   Total disponível: {len(all_stocks)} ações")
        print(f"   Excluídas recentes: {len(exclude_recent) if exclude_recent else 0}")
        
        return batch
    
    def get_top_liquidity_stocks(self, limit: int = 50) -> List[str]:
        """
        Obtém ações com maior liquidez (baseado em market cap)
        """
        all_stocks = self.get_all_b3_stocks()
        
        # Filtrar ações com market_cap
        stocks_with_cap = [s for s in all_stocks if s.get('market_cap')]
        
        # Ordenar por market cap (decrescente)
        stocks_with_cap.sort(key=lambda x: x['market_cap'], reverse=True)
        
        # Extrair tickers top
        top_tickers = [stock['ticker'] for stock in stocks_with_cap[:limit]]
        
        print(f"📊 Top {len(top_tickers)} ações por market cap")
        for i, ticker in enumerate(top_tickers[:10], 1):
            print(f"   {i:2d}. {ticker}")
        
        if len(top_tickers) > 10:
            print(f"   ... e mais {len(top_tickers) - 10}")
        
        return top_tickers
    
    def get_stocks_by_sector(self, sector: str, limit: int = 20) -> List[str]:
        """
        Obtém ações por setor específico
        """
        all_stocks = self.get_all_b3_stocks()
        
        # Filtrar por setor
        sector_stocks = [s for s in all_stocks 
                       if s.get('sector', '').lower() == sector.lower()]
        
        # Ordenar por market cap
        sector_stocks.sort(key=lambda x: x['market_cap'] or 0, reverse=True)
        
        # Extrair tickers
        tickers = [stock['ticker'] for stock in sector_stocks[:limit]]
        
        print(f"🏢 {len(tickers)} ações do setor '{sector}'")
        for i, ticker in enumerate(tickers[:5], 1):
            print(f"   {i}. {ticker}")
        
        return tickers

def main():
    """Função principal para testes"""
    import sys
    
    finder = B3StockFinder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            print("LISTANDO AÇÕES DA B3")
            print("=" * 50)
            stocks = finder.get_all_b3_stocks()
            
            print(f"\nTotal encontrado: {len(stocks)} ações")
            print("\nPrimeiras 20 ações:")
            for i, stock in enumerate(stocks[:20], 1):
                print(f"{i:2d}. {stock['ticker']:6s} - {stock['name'][:30]}")
            
        elif command == "rotate":
            batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            print(f"GERANDO LOTE ROTACIONADO DE {batch_size} AÇÕES")
            print("=" * 50)
            
            batch = finder.get_rotated_stocks(batch_size=batch_size)
            
            print(f"\nLote gerado ({len(batch)} ações):")
            for i, ticker in enumerate(batch, 1):
                print(f"{i:2d}. {ticker}")
            
        elif command == "top":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            print(f"TOP {limit} AÇÕES POR LIQUIDEZ")
            print("=" * 50)
            
            top_stocks = finder.get_top_liquidity_stocks(limit=limit)
            
        elif command == "sector":
            if len(sys.argv) > 2:
                sector = sys.argv[2]
                limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
                print(f"AÇÕES DO SETOR: {sector.upper()}")
                print("=" * 50)
                
                sector_stocks = finder.get_stocks_by_sector(sector, limit)
            else:
                print("Uso: python b3_stock_finder.py sector <nome_setor> [limite]")
                
        else:
            print("Comandos disponíveis:")
            print("  python b3_stock_finder.py list                    - Listar todas as ações")
            print("  python b3_stock_finder.py rotate [tamanho]         - Gerar lote rotacionado")
            print("  python b3_stock_finder.py top [limite]             - Top ações por liquidez")
            print("  python b3_stock_finder.py sector <setor> [limite] - Ações por setor")
    else:
        print("Uso: python b3_stock_finder.py [list|rotate|top|sector]")

if __name__ == "__main__":
    main()