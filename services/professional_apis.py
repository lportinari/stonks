#!/usr/bin/env python3
"""
APIs Profissionais para Dados de Mercado
Alpha Vantage e BrAPI.dev com rate limiting robusto
"""
import requests
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ProfessionalAPIService:
    """Serviço de APIs profissionais para dados de mercado"""
    
    def __init__(self):
        # Configurações das APIs via variáveis de ambiente
        from config import Config
        self.alphavantage_api_key = Config.ALPHAVANTAGE_API_KEY
        self.brapi_api_key = Config.BRAPI_API_KEY
        
        # Rate limiting
        self.requests_per_minute = 5  # Alphavantage free tier
        self.last_request_time = {}
        self.min_request_interval = 60 / self.requests_per_minute  # 12 segundos
        
        # Headers comuns
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
        }
    
    def _rate_limit_check(self, api_name: str):
        """Verifica e respeita rate limiting"""
        now = time.time()
        last_time = self.last_request_time.get(api_name, 0)
        
        if now - last_time < self.min_request_interval:
            wait_time = self.min_request_interval - (now - last_time)
            logger.info(f"Rate limiting {api_name}: aguardando {wait_time:.1f}s")
            time.sleep(wait_time)
        
        self.last_request_time[api_name] = time.time()
    
    def get_from_alphavantage(self, ticker: str) -> Optional[Dict]:
        """
        Obtém dados do Alpha Vantage
        Free tier: 5 requests/minute, 500 requests/day
        """
        try:
            self._rate_limit_check('alphavantage')
            
            # Alpha Vantage Global Quote
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': f'{ticker}.SA',  # Sufixo para B3
                'apikey': self.alphavantage_api_key
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar se há erro ou limite atingido
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return None
                
                if 'Note' in data:
                    logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                    return None
                
                # Extrair dados do Global Quote
                quote_data = data.get('Global Quote', {})
                if quote_data:
                    price_str = quote_data.get('05. price', '0')
                    change_str = quote_data.get('09. change', '0')
                    change_percent_str = quote_data.get('10. change percent', '0')
                    
                    return {
                        'success': True,
                        'ticker': ticker,
                        'cotacao': float(price_str) if price_str.replace('.', '').replace('-', '').isdigit() else None,
                        'variacao': float(change_str) if change_str.replace('.', '').replace('-', '').isdigit() else None,
                        'variacao_percent': float(change_percent_str.replace('%', '')) if change_percent_str.replace('%', '').replace('.', '').replace('-', '').isdigit() else None,
                        'empresa': f'Empresa {ticker}',
                        'fonte_dados': 'alphavantage',
                        'data_atualizacao': datetime.now().isoformat(),
                        'volume': quote_data.get('06. volume'),
                        'horario': quote_data.get('07. latest trading day')
                    }
            
            elif response.status_code == 429:
                logger.warning("Alpha Vantage rate limit atingido")
            
        except Exception as e:
            logger.error(f"Erro Alpha Vantage para {ticker}: {e}")
        
        return None
    
    def get_from_brapi(self, ticker: str) -> Optional[Dict]:
        """
        Obtém dados do BrAPI.dev
        API brasileira com dados completos da B3
        """
        try:
            self._rate_limit_check('brapi')
            
            # BrAPI Quote endpoint
            url = f"https://brapi.dev/api/quote/{ticker}"
            params = {
                'token': self.brapi_api_key,
                'fundamental': 'true'  # Incluir dados fundamentais
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results') and len(data['results']) > 0:
                    stock_data = data['results'][0]
                    
                    return {
                        'success': True,
                        'ticker': ticker,
                        'cotacao': stock_data.get('regularMarketPrice'),
                        'empresa': stock_data.get('longName') or stock_data.get('shortName'),
                        'short_name': stock_data.get('shortName'),
                        'setor': stock_data.get('sector'),
                        'subsetor': stock_data.get('industry'),
                        'currency': stock_data.get('currency', 'BRL'),
                        'logo_url': stock_data.get('logourl'),
                        
                        # Variação e preços diários
                        'regular_market_day_high': stock_data.get('regularMarketDayHigh'),
                        'regular_market_day_low': stock_data.get('regularMarketDayLow'),
                        'regular_market_day_range': stock_data.get('regularMarketDayRange'),
                        'regular_market_change': stock_data.get('regularMarketChange'),
                        'regular_market_change_percent': stock_data.get('regularMarketChangePercent'),
                        'regular_market_time': stock_data.get('regularMarketTime'),
                        'regular_market_previous_close': stock_data.get('regularMarketPreviousClose'),
                        'regular_market_open': stock_data.get('regularMarketOpen'),
                        
                        # Dados de 52 semanas
                        'fifty_two_week_range': stock_data.get('fiftyTwoWeekRange'),
                        'fifty_two_week_low': stock_data.get('fiftyTwoWeekLow'),
                        'fifty_two_week_high': stock_data.get('fiftyTwoWeekHigh'),
                        
                        # Métricas adicionais
                        'price_earnings': stock_data.get('priceEarnings'),
                        'earnings_per_share': stock_data.get('earningsPerShare'),
                        
                        # Indicadores fundamentais
                        'div_yield': stock_data.get('dividendYield'),
                        'pl': stock_data.get('forwardPE') or stock_data.get('trailingPE'),
                        'pvp': stock_data.get('priceToBook'),
                        'roe': stock_data.get('returnOnEquity'),
                        'margem_liquida': stock_data.get('profitMargins'),
                        'ev_ebitda': stock_data.get('enterpriseToEbitda'),
                        'psr': stock_data.get('priceToSales'),
                        'liquidez_corrente': stock_data.get('currentRatio'),
                        'div_liquida_patrim': stock_data.get('debtToEquity'),
                        'roic': stock_data.get('returnOnAssets'),
                        'cresc_receita_5a': stock_data.get('revenueGrowth'),
                        
                        # Outros dados
                        'fonte_dados': 'brapi',
                        'data_atualizacao': datetime.now().isoformat(),
                        'volume': stock_data.get('regularMarketVolume'),
                        'market_cap': stock_data.get('marketCap'),
                        'moeda': stock_data.get('currency', 'BRL')
                    }
            
            elif response.status_code == 429:
                logger.warning("BrAPI rate limit atingido")
            
        except Exception as e:
            logger.error(f"Erro BrAPI para {ticker}: {e}")
        
        return None
    
    def get_all_indicators_brapi(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Obtém indicadores completos para múltiplos tickers via BrAPI
        """
        try:
            self._rate_limit_check('brapi')
            
            # Batch request para múltiplos tickers
            ticker_str = ','.join(tickers)
            url = f"https://brapi.dev/api/quote/{ticker_str}"
            params = {
                'token': self.brapi_api_key,
                'fundamental': 'true',
                'metrics': 'all'  # Todos os métricas disponíveis
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                results = {}
                
                if data.get('results'):
                    for stock_data in data['results']:
                        ticker = stock_data.get('symbol')
                        if ticker:
                            results[ticker] = {
                                'success': True,
                                'ticker': ticker,
                                'cotacao': stock_data.get('regularMarketPrice'),
                                'empresa': stock_data.get('longName') or stock_data.get('shortName'),
                                'short_name': stock_data.get('shortName'),
                                'setor': stock_data.get('sector'),
                                'subsetor': stock_data.get('industry'),
                                'currency': stock_data.get('currency', 'BRL'),
                                'logo_url': stock_data.get('logourl'),
                                
                                # Variação e preços diários
                                'regular_market_day_high': stock_data.get('regularMarketDayHigh'),
                                'regular_market_day_low': stock_data.get('regularMarketDayLow'),
                                'regular_market_day_range': stock_data.get('regularMarketDayRange'),
                                'regular_market_change': stock_data.get('regularMarketChange'),
                                'regular_market_change_percent': stock_data.get('regularMarketChangePercent'),
                                'regular_market_time': stock_data.get('regularMarketTime'),
                                'regular_market_previous_close': stock_data.get('regularMarketPreviousClose'),
                                'regular_market_open': stock_data.get('regularMarketOpen'),
                                
                                # Dados de 52 semanas
                                'fifty_two_week_range': stock_data.get('fiftyTwoWeekRange'),
                                'fifty_two_week_low': stock_data.get('fiftyTwoWeekLow'),
                                'fifty_two_week_high': stock_data.get('fiftyTwoWeekHigh'),
                                
                                # Métricas adicionais
                                'price_earnings': stock_data.get('priceEarnings'),
                                'earnings_per_share': stock_data.get('earningsPerShare'),
                                
                                # Indicadores fundamentais
                                'div_yield': stock_data.get('dividendYield'),
                                'pl': stock_data.get('forwardPE') or stock_data.get('trailingPE'),
                                'pvp': stock_data.get('priceToBook'),
                                'roe': stock_data.get('returnOnEquity'),
                                'margem_liquida': stock_data.get('profitMargins'),
                                'ev_ebitda': stock_data.get('enterpriseToEbitda'),
                                'psr': stock_data.get('priceToSales'),
                                'liquidez_corrente': stock_data.get('currentRatio'),
                                'div_liquida_patrim': stock_data.get('debtToEquity'),
                                'roic': stock_data.get('returnOnAssets'),
                                'cresc_receita_5a': stock_data.get('revenueGrowth'),
                                
                                'fonte_dados': 'brapi_batch',
                                'data_atualizacao': datetime.now().isoformat(),
                                'volume': stock_data.get('regularMarketVolume'),
                                'market_cap': stock_data.get('marketCap'),
                                'moeda': stock_data.get('currency', 'BRL')
                            }
                
                return results
            
        except Exception as e:
            logger.error(f"Erro batch BrAPI: {e}")
        
        return {}
    
    def get_professional_data(self, ticker: str) -> Optional[Dict]:
        """
        Obtém dados profissionais usando múltiplas APIs em ordem de prioridade
        """
        # Ordem de prioridade: BrAPI (mais completa) -> Alpha Vantage
        sources = [
            (self.get_from_brapi, 'BrAPI'),
            (self.get_from_alphavantage, 'Alpha Vantage')
        ]
        
        for source_func, source_name in sources:
            try:
                data = source_func(ticker)
                
                if data and data.get('success') and data.get('cotacao'):
                    logger.info(f"{ticker}: Dados obtidos de {source_name} - R$ {data['cotacao']}")
                    return data
                else:
                    logger.warning(f"{ticker}: Falha em {source_name}")
                    
            except Exception as e:
                logger.error(f"{ticker}: Erro em {source_name}: {e}")
            
            # Delay entre fontes
            time.sleep(2)
        
        logger.error(f"{ticker}: Todas as APIs profissionais falharam")
        return None
    
    def test_apis(self) -> Dict:
        """Testa ambas as APIs profissionais"""
        print("TESTANDO APIs PROFISSIONAIS")
        print("=" * 50)
        
        test_ticker = 'PETR4'
        results = {}
        
        # Testar BrAPI
        print("\nTestando BrAPI...")
        try:
            data = self.get_from_brapi(test_ticker)
            if data and data.get('success'):
                results['BrAPI'] = '✅ OK'
                print(f"   ✅ BrAPI: FUNCIONANDO")
                print(f"   📈 Preço: R$ {data.get('cotacao', 'N/A')}")
                print(f"   🏢 Empresa: {data.get('empresa', 'N/A')}")
                if data.get('div_yield'):
                    print(f"   💰 DY: {data['div_yield']:.2f}%")
            else:
                results['BrAPI'] = '❌ Falha'
                print(f"   ❌ BrAPI: FALHOU")
        except Exception as e:
            results['BrAPI'] = f'❌ Erro: {str(e)[:20]}...'
            print(f"   ❌ BrAPI: ERRO - {e}")
        
        # Testar Alpha Vantage
        print("\nTestando Alpha Vantage...")
        try:
            data = self.get_from_alphavantage(test_ticker)
            if data and data.get('success'):
                results['Alpha Vantage'] = '✅ OK'
                print(f"   ✅ Alpha Vantage: FUNCIONANDO")
                print(f"   📈 Preço: R$ {data.get('cotacao', 'N/A')}")
                if data.get('variacao_percent'):
                    print(f"   📊 Variação: {data['variacao_percent']:+.2f}%")
            else:
                results['Alpha Vantage'] = '❌ Falha'
                print(f"   ❌ Alpha Vantage: FALHOU")
        except Exception as e:
            results['Alpha Vantage'] = f'❌ Erro: {str(e)[:20]}...'
            print(f"   ❌ Alpha Vantage: ERRO - {e}")
        
        print(f"\n📋 RESUMO:")
        for api, status in results.items():
            print(f"   {api}: {status}")
        
        return results

# Função wrapper para compatibilidade
def get_professional_stocks_data(tickers: List[str]) -> Dict[str, Dict]:
    """Função wrapper para obter dados profissionais"""
    api_service = ProfessionalAPIService()
    
    # Tentar batch request primeiro (BrAPI)
    if len(tickers) > 1:
        print("Tentando batch request via BrAPI...")
        batch_data = api_service.get_all_indicators_brapi(tickers)
        
        if batch_data:
            print(f"Batch successful: {len(batch_data)} tickers obtidos")
            return batch_data
        else:
            print("Batch failed, tentando individual...")
    
    # Fallback para requests individuais
    results = {}
    for ticker in tickers:
        print(f"Buscando {ticker} individualmente...")
        data = api_service.get_professional_data(ticker)
        if data:
            results[ticker] = data
        
        # Delay entre tickers individuais
        time.sleep(3)
    
    return results

if __name__ == "__main__":
    # Testar APIs
    api_service = ProfessionalAPIService()
    api_service.test_apis()
    
    print("\n" + "=" * 50)
    print("BUSCANDO DADOS PROFISSIONAIS (TOP 3)")
    print("=" * 50)
    
    # Testar com top 3 tickers
    test_tickers = ['PETR4', 'VALE3', 'ITUB4']
    professional_data = get_professional_stocks_data(test_tickers)
    
    print(f"\n📊 RESULTADO FINAL:")
    for ticker, data in professional_data.items():
        if data.get('success'):
            print(f"✅ {ticker}: R$ {data.get('cotacao', 0):.2f} ({data.get('fonte_dados', 'unknown')})")
        else:
            print(f"❌ {ticker}: Falha")