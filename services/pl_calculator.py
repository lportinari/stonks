import requests
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from models.stock import Stock
from services.professional_apis import ProfessionalAPIService
from config import Config

logger = logging.getLogger(__name__)

class PLCalculator:
    """Serviço responsável por calcular e enriquecer dados de PL para as ações"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.brapi_service = ProfessionalAPIService()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def calculate_pl_for_stock(self, stock: Stock) -> Optional[float]:
        """
        Calcula PL para uma ação específica usando múltiplas fontes
        
        Args:
            stock: Objeto Stock da ação
            
        Returns:
            float: Valor do PL calculado ou None
        """
        ticker = stock.ticker
        
        # Tentativa 1: Usar price_earnings da BrAPI (já disponível)
        if stock.price_earnings and stock.price_earnings > 0:
            logger.debug(f"PL para {ticker} encontrado na BrAPI: {stock.price_earnings}")
            return stock.price_earnings
        
        # Tentativa 2: Calcular PL = Preço da Ação / Lucro por Ação
        if stock.cotacao and stock.earnings_per_share and stock.earnings_per_share > 0:
            pl_calculado = stock.cotacao / stock.earnings_per_share
            logger.debug(f"PL para {ticker} calculado: {pl_calculado:.2f}")
            return pl_calculado
        
        # Tentativa 3: Obter dados da BrAPI em tempo real
        try:
            brapi_data = self.brapi_service.get_from_brapi(ticker)
            if brapi_data and 'price_earnings' in brapi_data:
                pl = brapi_data['price_earnings']
                if pl and pl > 0:
                    logger.debug(f"PL para {ticker} obtido da BrAPI: {pl}")
                    return pl
                    
            # Se não tiver PL direto, tentar calcular com dados da BrAPI
            if (brapi_data and 'cotacao' in brapi_data and 
                'earnings_per_share' in brapi_data):
                price = brapi_data['cotacao']
                eps = brapi_data['earnings_per_share']
                if price and eps and eps > 0:
                    pl_calculado = price / eps
                    logger.debug(f"PL para {ticker} calculado via BrAPI: {pl_calculado:.2f}")
                    return pl_calculado
                    
        except Exception as e:
            logger.warning(f"Erro ao obter dados da BrAPI para {ticker}: {e}")
        
        # Tentativa 4: Yahoo Finance
        try:
            yahoo_data = self._get_yahoo_finance_data(ticker)
            if yahoo_data:
                # Tentar obter PE ratio do Yahoo
                if 'trailingPE' in yahoo_data and yahoo_data['trailingPE']:
                    pl = yahoo_data['trailingPE']
                    logger.debug(f"PL para {ticker} obtido do Yahoo Finance: {pl}")
                    return pl
                
                # Tentar calcular com dados do Yahoo
                if ('currentPrice' in yahoo_data and 
                    'earningsPerShare' in yahoo_data and 
                    yahoo_data['earningsPerShare'] and 
                    yahoo_data['earningsPerShare'] > 0):
                    pl_calculado = yahoo_data['currentPrice'] / yahoo_data['earningsPerShare']
                    logger.debug(f"PL para {ticker} calculado via Yahoo: {pl_calculado:.2f}")
                    return pl_calculado
                    
        except Exception as e:
            logger.warning(f"Erro ao obter dados do Yahoo Finance para {ticker}: {e}")
        
        logger.warning(f"Não foi possível calcular PL para {ticker}")
        return None
    
    def _get_yahoo_finance_data(self, ticker: str) -> Optional[Dict]:
        """Obtém dados do Yahoo Finance usando API pública"""
        try:
            # Adicionar .SA para ações brasileiras
            if not ticker.endswith(('.34', '.35')):  # BDRs não usam .SA
                yahoo_ticker = f"{ticker}.SA"
            else:
                yahoo_ticker = ticker
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_ticker}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('chart') and data['chart'].get('result'):
                    result = data['chart']['result'][0]
                    meta = result.get('meta', {})
                    
                    return {
                        'currentPrice': meta.get('regularMarketPrice'),
                        'trailingPE': meta.get('trailingPE'),
                        'earningsPerShare': meta.get('epsTrailingTwelveMonths')
                    }
                    
        except Exception as e:
            logger.debug(f"Erro ao consultar Yahoo Finance para {ticker}: {e}")
            
        return None
    
    def update_pl_for_all_stocks(self, limit: int = None) -> Dict[str, int]:
        """
        Atualiza PL para todas as ações que não têm valor
        
        Args:
            limit: Limite de ações a processar (para testes)
            
        Returns:
            Dict: Estatísticas da atualização
        """
        stats = {
            'total_processed': 0,
            'pl_updated': 0,
            'pl_not_found': 0,
            'errors': 0
        }
        
        # Buscar ações que não têm PL ou têm PL inválido
        query = self.db.query(Stock).filter(
            (Stock.pl.is_(None)) | 
            (Stock.pl <= 0) |
            (Stock.pl > 1000)  # PL acima de 1000 provavelmente é erro
        )
        
        if limit:
            query = query.limit(limit)
        
        stocks = query.all()
        logger.info(f"Processando {len(stocks)} ações para atualização de PL")
        
        for stock in stocks:
            try:
                stats['total_processed'] += 1
                
                # Verificar classe de ativo - FIIs e ETFs têm tratamento especial
                if self._needs_special_pl_treatment(stock.ticker):
                    logger.debug(f"Pulando {stock.ticker} - classe de ativo especial")
                    continue
                
                new_pl = self.calculate_pl_for_stock(stock)
                
                if new_pl and 0 < new_pl < 1000:  # Validação básica
                    stock.pl = new_pl
                    stock.fonte_dados = f"{stock.fonte_dados}+PL_CALC"
                    stats['pl_updated'] += 1
                    logger.debug(f"PL atualizado para {stock.ticker}: {new_pl:.2f}")
                else:
                    stats['pl_not_found'] += 1
                    logger.debug(f"PL não encontrado para {stock.ticker}")
                
                # Salvar a cada 10 atualizações para não sobrecarregar
                if stats['total_processed'] % 10 == 0:
                    self.db.commit()
                    
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Erro ao processar PL para {stock.ticker}: {e}")
        
        # Commit final
        self.db.commit()
        
        logger.info(f"Atualização de PL concluída: {stats}")
        return stats
    
    def _needs_special_pl_treatment(self, ticker: str) -> bool:
        """
        Verifica se o ativo precisa de tratamento especial para PL
        
        Returns:
            bool: True se for FII ou ETF
        """
        # FIIs usam P/VPA em vez de P/L
        if ticker.endswith('11') and not ticker.startswith(('BOVA', 'BRAX', 'IVVB', 'SMAC', 'ECOO')):
            return True
        
        # ETFs têm tratamento específico
        if ticker.startswith(('BOVA', 'BRAX', 'IVVB', 'SMAC', 'ECOO', 'SPXI')):
            return True
        
        return False
    
    def get_pl_statistics(self) -> Dict:
        """Retorna estatísticas sobre a cobertura de PL no banco"""
        total = self.db.query(Stock).count()
        with_pl = self.db.query(Stock).filter(Stock.pl.isnot(None)).count()
        without_pl = total - with_pl
        
        # Estatísticas por classe de ativo
        fii_count = self.db.query(Stock).filter(Stock.ticker.like('%11')).count()
        
        # Corrigir query de ETFs
        etf_count = 0
        etf_prefixes = ['BOVA', 'BRAX', 'IVVB', 'SMAC', 'ECOO', 'SPXI']
        for prefix in etf_prefixes:
            etf_count += self.db.query(Stock).filter(Stock.ticker.startswith(prefix)).count()
        
        stock_count = total - fii_count - etf_count
        
        return {
            'total_stocks': total,
            'with_pl': with_pl,
            'without_pl': without_pl,
            'coverage_percentage': (with_pl / total * 100) if total > 0 else 0,
            'by_asset_class': {
                'acoes': stock_count,
                'fii': fii_count,
                'etf': etf_count
            }
        }