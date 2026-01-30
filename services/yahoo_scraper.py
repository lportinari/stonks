#!/usr/bin/env python3
"""
Scraper de dados do Yahoo Finance para ações brasileiras
Usa yfinance para obter dados fundamentalistas em tempo real
"""

import yfinance as yf
import pandas as pd
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class YahooFinanceScraper:
    """Classe para scraping de dados do Yahoo Finance"""
    
    def __init__(self):
        self.session = None
        
        # Lista principal de ações brasileiras (IBOVESPA + principais)
        self.tickers_br = [
            # Bancos
            'ITUB4.SA', 'BBDC4.SA', 'BBAS3.SA', 'SANB11.SA', 'B3SA3.SA',
            
            # Petróleo e Gás
            'PETR4.SA', 'PRIO3.SA', 'EQTL3.SA', 'UGPA3.SA',
            
            # Mineração
            'VALE3.SA', 'CSNA3.SA',
            
            # Siderurgia
            'GGBR4.SA', 'CSAN3.SA',
            
            # Energia Elétrica
            'ELET3.SA', 'ENBR3.SA', 'EQTL3.SA', 'TAEE11.SA', 'CMIG4.SA',
            
            # Varejo
            'MGLU3.SA', 'LREN3.SA', 'WIZS3.SA', 'AMER3.SA',
            
            # Bens de Consumo
            'ABEV3.SA', 'MGLU3.SA', 'NTCO3.SA', 'SLCE3.SA',
            
            # Tecnologia
            'WEGE3.SA', 'TOTS3.SA', 'POS311.SA', 'MEAL3.SA',
            
            # Saúde
            'RADL3.SA', 'HAPV3.SA', 'QUAL3.SA', 'DIMS3.SA',
            
            # Construção
            'CYRE3.SA', 'MRFG3.SA', 'EZTC3.SA', 'JHSF3.SA',
            
            # Alimentos
            'JBSS3.SA', 'BRFS3.SA', 'MGLU3.SA',
            
            # Papel e Celulose
            'SUZB3.SA', 'KLBN11.SA',
            
            # Telecomunicações
            'VIVT3.SA', 'TIMS3.SA', 'OI3.SA',
            
            # Transporte
            'GOLL4.SA', 'AZUL4.SA', 'CCRO3.SA',
            
            # Química e Petróleo
            'BRKM5.SA', 'RAIL3.SA',
            
            # Outros
            'RENT3.SA', 'LAME4.SA', 'CRFB3.SA', 'PCAR3.SA'
        ]
        
        # Remover duplicatas
        self.tickers_br = list(set(self.tickers_br))
        logger.info(f"Configurados {len(self.tickers_br)} tickers para análise")
    
    def test_connection(self) -> bool:
        """Testa conexão com Yahoo Finance"""
        try:
            ticker = yf.Ticker('PETR4.SA')
            info = ticker.info
            return 'symbol' in info or 'longName' in info
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def get_stocks_data(self, max_stocks: int = None) -> List[Dict]:
        """Obtém dados de todas as ações configuradas"""
        logger.info("Iniciando coleta de dados do Yahoo Finance...")
        
        all_stocks = []
        tickers_to_process = self.tickers_br[:max_stocks] if max_stocks else self.tickers_br
        
        total = len(tickers_to_process)
        
        for i, ticker_symbol in enumerate(tickers_to_process, 1):
            try:
                logger.info(f"Processando {i}/{total}: {ticker_symbol}")
                
                # Obter dados do ticker
                ticker = yf.Ticker(ticker_symbol)
                
                # Tentar obter informações básicas
                info = ticker.info
                
                if not info or not info.get('symbol'):
                    logger.warning(f"Sem dados para {ticker_symbol}")
                    continue
                
                # Extrair dados fundamentalistas
                stock_data = self._extract_stock_data(ticker_symbol, info, ticker)
                
                if stock_data:
                    all_stocks.append(stock_data)
                    logger.info(f"Dados extraídos para {stock_data['ticker']}")
                
                # Delay para não sobrecarregar a API
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Erro ao processar {ticker_symbol}: {e}")
                continue
        
        logger.info(f"Coleta concluída. {len(all_stocks)} ações obtidas.")
        return all_stocks
    
    def _extract_stock_data(self, ticker_symbol: str, info: Dict, ticker_obj) -> Optional[Dict]:
        """Extrai e formata os dados de uma ação"""
        try:
            # Dados básicos
            ticker_br = ticker_symbol.replace('.SA', '')
            
            # Valores padrão
            stock_data = {
                'ticker': ticker_br,
                'empresa': info.get('longName', 'N/A'),
                'setor': info.get('sector', 'N/A'),
                'subsetor': info.get('industry', 'N/A'),
                'cotacao': None,
                'div_yield': None,
                'pl': None,
                'pvp': None,
                'roe': None,
                'margem_liquida': None,
                'ev_ebit': None,
                'ev_ebitda': None,
                'psr': None,
                'roic': None,
                'margem_ebit': None,
                'liquidity': None,
                'giro_ativos': None
            }
            
            # Obter dados financeiros
            financial_data = ticker_obj.financials
            balance_sheet = ticker_obj.balance_sheet
            cash_flow = ticker_obj.cashflow
            
            # Cotação atual
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if current_price and current_price > 0:
                stock_data['cotacao'] = float(current_price)
            
            # Dividend Yield
            div_yield = info.get('dividendYield')
            if div_yield and div_yield > 0:
                stock_data['div_yield'] = float(div_yield * 100)  # Converter para %
            
            # P/L Ratio
            pe_ratio = info.get('forwardPE') or info.get('trailingPE')
            if pe_ratio and abs(pe_ratio) < 1000:  # Filtrar valores absurdos
                stock_data['pl'] = float(pe_ratio)
            
            # P/VP Ratio
            pb_ratio = info.get('priceToBook')
            if pb_ratio and abs(pb_ratio) < 100:
                stock_data['pvp'] = float(pb_ratio)
            
            # ROE (Return on Equity)
            roe = info.get('returnOnEquity')
            if roe and abs(roe) < 10:  # ROE normalmente está em formato decimal
                stock_data['roe'] = float(roe * 100)  # Converter para %
            
            # Margem Líquida
            profit_margins = info.get('profitMargins')
            if profit_margins and abs(profit_margins) < 10:
                stock_data['margem_liquida'] = float(profit_margins * 100)  # Converter para %
            
            # EV/EBIT
            enterprise_to_ebitda = info.get('enterpriseToEbitda')
            if enterprise_to_ebitda and enterprise_to_ebitda > 0:
                stock_data['ev_ebitda'] = float(enterprise_to_ebitda)
            
            # Price to Sales (P/S)
            price_to_sales = info.get('priceToSalesTrailing12Months')
            if price_to_sales and price_to_sales > 0:
                stock_data['psr'] = float(price_to_sales)
            
            # ROIC
            roic = info.get('returnOnAssets')
            if roic and abs(roic) < 10:
                stock_data['roic'] = float(roic * 100)
            
            # Margem EBIT
            try:
                if not financial_data.empty:
                    # Tentar calcular margem EBIT a partir dos dados financeiros
                    ebit = financial_data.loc['EBIT'].iloc[0] if 'EBIT' in financial_data.index else None
                    revenue = financial_data.loc['Total Revenue'].iloc[0] if 'Total Revenue' in financial_data.index else None
                    
                    if ebit and revenue and revenue != 0:
                        ebit_margin = (ebit / revenue) * 100
                        if abs(ebit_margin) < 100:
                            stock_data['margem_ebit'] = float(ebit_margin)
            except:
                pass
            
            # Liquidez Corrente
            current_ratio = info.get('currentRatio')
            if current_ratio and current_ratio > 0:
                stock_data['liquidity'] = float(current_ratio)
            
            # Validar dados mínimos para incluir no ranking
            if self._validate_stock_data(stock_data):
                return stock_data
            else:
                logger.warning(f"Dados insuficientes para {ticker_br}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao extrair dados de {ticker_symbol}: {e}")
            return None
    
    def _validate_stock_data(self, stock_data: Dict) -> bool:
        """Valida se a ação tem dados mínimos para análise"""
        required_fields = ['ticker', 'cotacao']
        
        for field in required_fields:
            if not stock_data.get(field):
                return False
        
        # Verificar se pelo menos alguns indicadores estão presentes
        indicators = ['div_yield', 'pl', 'pvp', 'roe', 'margem_liquida']
        valid_indicators = sum(1 for ind in indicators if stock_data.get(ind) is not None)
        
        return valid_indicators >= 2  # Pelo menos 2 indicadores
    
    def get_specific_stock(self, ticker: str) -> Optional[Dict]:
        """Obtém dados de uma ação específica"""
        ticker_symbol = ticker if ticker.endswith('.SA') else f"{ticker}.SA"
        
        try:
            ticker_obj = yf.Ticker(ticker_symbol)
            info = ticker_obj.info
            
            if not info or not info.get('symbol'):
                return None
            
            return self._extract_stock_data(ticker_symbol, info, ticker_obj)
            
        except Exception as e:
            logger.error(f"Erro ao obter dados de {ticker}: {e}")
            return None
    
    def get_market_status(self) -> Dict:
        """Obtém status geral do mercado"""
        try:
            # Obter dados do índice Bovespa
            bovespa = yf.Ticker('^BVSP')
            bovespa_info = bovespa.info
            
            # Obter dados do Dólar
            usd_brl = yf.Ticker('USDBRL=X')
            usd_info = usd_brl.info
            
            return {
                'bovespa': {
                    'value': bovespa_info.get('regularMarketPrice'),
                    'change': bovespa_info.get('regularMarketChange'),
                    'change_percent': bovespa_info.get('regularMarketChangePercent')
                },
                'dollar': {
                    'value': usd_info.get('regularMarketPrice'),
                    'change': usd_info.get('regularMarketChange'),
                    'change_percent': usd_info.get('regularMarketChangePercent')
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status do mercado: {e}")
            return {}

# Função para compatibilidade com código existente
def get_stocks_data(max_stocks: int = None) -> List[Dict]:
    """Função wrapper para compatibilidade"""
    scraper = YahooFinanceScraper()
    return scraper.get_stocks_data(max_stocks)

def test_connection() -> bool:
    """Função wrapper para testar conexão"""
    scraper = YahooFinanceScraper()
    return scraper.test_connection()

if __name__ == "__main__":
    # Teste do scraper
    scraper = YahooFinanceScraper()
    
    print("Testando conexão...")
    if scraper.test_connection():
        print("✅ Conexão OK!")
        
        print("\nObtendo dados de exemplo (5 ações)...")
        stocks = scraper.get_stocks_data(max_stocks=5)
        
        print(f"\nDados obtidos: {len(stocks)} ações")
        for stock in stocks:
            print(f"\n{stock['ticker']} - {stock['empresa']}")
            print(f"  Setor: {stock['setor']}")
            print(f"  Cotação: R$ {stock['cotacao']:.2f}")
            print(f"  DY: {stock['div_yield']:.2f}%" if stock['div_yield'] else "  DY: N/A")
            print(f"  P/L: {stock['pl']:.2f}" if stock['pl'] else "  P/L: N/A")
            print(f"  P/VP: {stock['pvp']:.2f}" if stock['pvp'] else "  P/VP: N/A")
    else:
        print("❌ Falha na conexão!")