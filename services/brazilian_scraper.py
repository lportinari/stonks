#!/usr/bin/env python3
"""
Scraper Brasileiro - Fontes de Dados Nacionais
Solução alternativa ao Yahoo Finance com APIs brasileiras
"""

import requests
import json
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class BrazilianScraper:
    """Scraper focado em fontes brasileiras de dados"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_delay = 1.0
        
        # Headers para simular navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/',
        }
        
        self.session.headers.update(self.headers)
    
    def get_from_status_invest(self, ticker: str) -> Optional[Dict]:
        """
        Obtém dados do Status Invest
        API brasileira confiável e atualizada
        """
        try:
            # Status Invest API endpoints
            urls = [
                f"https://api.statusinvest.com.br/asset/v1/search?q={ticker}",
                f"https://api.statusinvest.com.br/asset/v1/assets/{ticker}",
                f"https://statusinvest.com.br/api/company/search?q={ticker}"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Parse diferente dependendo do endpoint
                        if isinstance(data, list) and len(data) > 0:
                            # Search endpoint
                            asset_data = data[0]
                        elif isinstance(data, dict):
                            # Direct asset endpoint
                            asset_data = data
                        else:
                            continue
                        
                        # Extrair dados
                        return {
                            'success': True,
                            'ticker': ticker,
                            'cotacao': asset_data.get('price') or asset_data.get('price_earnings'),
                            'empresa': asset_data.get('company_name') or asset_data.get('name'),
                            'setor': asset_data.get('sector'),
                            'div_yield': asset_data.get('dividend_yield'),
                            'pl': asset_data.get('price_earnings'),
                            'pvp': asset_data.get('price_book_value'),
                            'roe': asset_data.get('roe'),
                            'margem_liquida': asset_data.get('net_margin'),
                            'fonte_dados': 'status_invest',
                            'data_atualizacao': datetime.now().isoformat()
                        }
                
                except Exception as e:
                    logger.warning(f"Status Invest endpoint {url} falhou: {e}")
                    continue
                
                # Delay entre tentativas
                time.sleep(self.base_delay)
        
        except Exception as e:
            logger.error(f"Status Invest erro geral: {e}")
        
        return None
    
    def get_from_infomoney(self, ticker: str) -> Optional[Dict]:
        """
        Obtém dados do InfoMoney
        Fonte confiável de mercado brasileiro
        """
        try:
            # InfoMoney endpoints
            urls = [
                f"https://www.infomoney.com.br/api/cotacoes/bolsa/acoes/{ticker.lower()}",
                f"https://api.infomoney.com.br/cotacoes/{ticker}",
                f"https://infomoney.com.br/cotacoes/{ticker.lower()}"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        return {
                            'success': True,
                            'ticker': ticker,
                            'cotacao': data.get('cotacao') or data.get('price') or data.get('ultimo'),
                            'empresa': data.get('empresa') or data.get('name'),
                            'div_yield': data.get('dy') or data.get('dividend_yield'),
                            'pl': data.get('pl') or data.get('price_earnings'),
                            'pvp': data.get('pvp') or data.get('price_book'),
                            'fonte_dados': 'infomoney',
                            'data_atualizacao': datetime.now().isoformat()
                        }
                
                except Exception as e:
                    logger.warning(f"InfoMoney endpoint {url} falhou: {e}")
                    continue
                
                time.sleep(self.base_delay)
        
        except Exception as e:
            logger.error(f"InfoMoney erro geral: {e}")
        
        return None
    
    def get_from_uol_economia(self, ticker: str) -> Optional[Dict]:
        """
        Obtém dados do UOL Economia
        Fonte brasileira tradicional
        """
        try:
            # UOL Economia endpoints
            urls = [
                f"https://economia.uol.com.br/cotacoes/bolsas/acoes-bovespa/{ticker.lower()}/",
                f"https://api.uol.com.br/economia/cotacoes/{ticker}"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        # UOL geralmente retorna HTML, precisa parse
                        # Por ora, retorna estrutura básica
                        return {
                            'success': True,
                            'ticker': ticker,
                            'cotacao': None,  # Precisaria de HTML parsing
                            'empresa': f'Empresa {ticker}',
                            'fonte_dados': 'uol_economia',
                            'data_atualizacao': datetime.now().isoformat()
                        }
                
                except Exception as e:
                    logger.warning(f"UOL endpoint {url} falhou: {e}")
                    continue
                
                time.sleep(self.base_delay)
        
        except Exception as e:
            logger.error(f"UOL erro geral: {e}")
        
        return None
    
    def get_from_br_investing(self, ticker: str) -> Optional[Dict]:
        """
        Obtém dados do Investing.com Brasil
        Fonte internacional com dados brasileiros
        """
        try:
            # Investing.com endpoints
            urls = [
                f"https://br.investing.com/api/quotes/{ticker.lower()}",
                f"https://www.investing.com/api/quotes/{ticker.lower()}",
                f"https://api.investing.com/api/v1/quotes/{ticker.lower()}"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        return {
                            'success': True,
                            'ticker': ticker,
                            'cotacao': data.get('price') or data.get('last'),
                            'empresa': data.get('name'),
                            'div_yield': data.get('dividend_yield'),
                            'pl': data.get('price_earnings'),
                            'pvp': data.get('price_book'),
                            'fonte_dados': 'br_investing',
                            'data_atualizacao': datetime.now().isoformat()
                        }
                
                except Exception as e:
                    logger.warning(f"Investing endpoint {url} falhou: {e}")
                    continue
                
                time.sleep(self.base_delay)
        
        except Exception as e:
            logger.error(f"Investing erro geral: {e}")
        
        return None
    
    def get_real_quote(self, ticker: str) -> Optional[Dict]:
        """
        Obtém cotação real tentando múltiplas fontes brasileiras
        
        Args:
            ticker: Ticker da ação
            
        Returns:
            Dict com dados da ação ou None
        """
        print(f"🔍 Buscando {ticker} em fontes brasileiras...")
        
        # Ordem de prioridade: brasileiras primeiro
        sources = [
            self.get_from_status_invest,
            self.get_from_infomoney,
            self.get_from_br_investing,
            self.get_from_uol_economia
        ]
        
        for source_func in sources:
            try:
                data = source_func(ticker)
                
                if data and data.get('success') and data.get('cotacao'):
                    print(f"✅ {ticker}: R$ {data['cotacao']:.2f} ({data['fonte_dados']})")
                    return data
                elif data and data.get('success'):
                    print(f"⚠️ {ticker}: Sem preço em {data['fonte_dados']}")
                else:
                    print(f"❌ {ticker}: Falha em {source_func.__name__}")
                
            except Exception as e:
                print(f"❌ {ticker}: Erro em {source_func.__name__}: {e}")
            
            # Delay entre fontes
            time.sleep(self.base_delay)
        
        print(f"❌ {ticker}: Todas as fontes falharam")
        return None
    
    def get_all_real_quotes(self, tickers: List[str] = None) -> List[Dict]:
        """
        Obtém cotações reais para múltiplas ações
        
        Args:
            tickers: Lista de tickers (usa padrão se None)
            
        Returns:
            Lista de ações com dados reais
        """
        if tickers is None:
            tickers = [
                'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
                'GGBR4', 'ABEV3', 'MGLU3', 'B3SA3', 'BBAS3',
                'SANB11', 'RAIL3', 'SUZB3', 'KLBN11', 'LREN3',
                'RADL3', 'ELET3', 'ENBR3'
            ]
        
        print(f"🔄 Buscando dados REAIS para {len(tickers)} ações...")
        print("🌍 Usando fontes brasileiras (Status Invest, InfoMoney, etc.)")
        print("⏱️  Processando com delays para evitar bloqueios...\n")
        
        results = []
        
        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] ", end="")
            
            data = self.get_real_quote(ticker)
            
            if data:
                results.append(data)
            else:
                # Dados mínimos se falhar tudo
                results.append({
                    'ticker': ticker,
                    'empresa': f'Empresa {ticker}',
                    'cotacao': None,
                    'div_yield': None,
                    'pl': None,
                    'pvp': None,
                    'roe': None,
                    'margem_liquida': None,
                    'fonte_dados': 'fallback_error',
                    'data_atualizacao': datetime.now().isoformat()
                })
            
            # Delay entre tickers
            if i < len(tickers):
                time.sleep(self.base_delay + random.uniform(0.5, 1.0))
        
        successful = len([r for r in results if r.get('cotacao')])
        print(f"\n📊 Resultado: {successful}/{len(tickers)} ações com preços reais")
        
        return results
    
    def test_sources(self) -> Dict:
        """Testa todas as fontes brasileiras"""
        print("🧪 TESTANDO FONTES BRASILEIRAS")
        print("=" * 40)
        
        test_ticker = 'PETR4'
        results = {}
        
        sources = [
            ('Status Invest', self.get_from_status_invest),
            ('InfoMoney', self.get_from_infomoney),
            ('Br Investing', self.get_from_br_investing),
            ('UOL Economia', self.get_from_uol_economia)
        ]
        
        for name, func in sources:
            try:
                print(f"\n🔍 Testando {name}...")
                data = func(test_ticker)
                
                if data and data.get('success') and data.get('cotacao'):
                    results[name] = '✅ OK'
                    print(f"   ✅ {name}: FUNCIONANDO")
                    print(f"   📈 Preço: R$ {data['cotacao']:.2f}")
                else:
                    results[name] = '❌ Falha'
                    print(f"   ❌ {name}: FALHOU")
                
            except Exception as e:
                results[name] = f'❌ Erro'
                print(f"   ❌ {name}: ERRO - {e}")
        
        print(f"\n📋 RESUMO:")
        for name, status in results.items():
            print(f"   {name}: {status}")
        
        return results

# Função wrapper para compatibilidade
def get_brazilian_stocks_data(max_stocks: int = None) -> List[Dict]:
    """Função wrapper para compatibilidade"""
    scraper = BrazilianScraper()
    
    tickers = [
        'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
        'GGBR4', 'ABEV3', 'MGLU3', 'B3SA3', 'BBAS3',
        'SANB11', 'RAIL3', 'SUZB3', 'KLBN11', 'LREN3',
        'RADL3', 'ELET3', 'ENBR3'
    ]
    
    if max_stocks:
        tickers = tickers[:max_stocks]
    
    return scraper.get_all_real_quotes(tickers)

if __name__ == "__main__":
    # Testar fontes
    scraper = BrazilianScraper()
    scraper.test_sources()
    
    print("\n" + "=" * 50)
    print("🔄 BUSCANDO DADOS REAIS (TOP 5)")
    print("=" * 50)
    
    # Buscar dados reais para top 5
    real_stocks = scraper.get_all_real_quotes(['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3'])
    
    print(f"\n📊 RESULTADO FINAL:")
    for i, stock in enumerate(real_stocks, 1):
        price = stock['cotacao']
        if price:
            print(f"{i}. {stock['ticker']}: R$ {price:.2f} ({stock['fonte_dados']})")
        else:
            print(f"{i}. {stock['ticker']}: SEM DADOS ({stock['fonte_dados']})")