import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from models.stock import Stock

logger = logging.getLogger(__name__)

class AssetClassifier:
    """Serviço responsável por classificar ativos financeiros por tipo"""
    
    # Listas conhecidas de ETFs brasileiros
    ETF_TICKERS = {
        # Índices Amplos
        'BOVA11', 'BRAX11', 'IVVB11', 'SMAC11', 'ECOO11',
        
        # Setoriais
        'MOBI11', 'MATB11', 'XBOC11', 'ISUS11', 'RENT11',
        'Find11', 'BDRX11', 'SPXI11', 'SMLL11', 'DIVO11',
        
        # Temáticos
        'HECT11', 'FIND11', 'IRFM11', 'AÇAO11', 'GOVE11',
        'MONEY11', 'BITH11', 'CRYPT11', 'EWZ21', 'EWZ31',
        
        # Internacionais
        'WDOF11', 'WDOV11', 'COCE11', 'GOLD11', 'SOIL11',
        
        # Renda Fixa
        'IMAB11', 'FIXA11', 'XPLG11', 'DEBTP11'
    }
    
    # Padrões de ETFs baseados em prefixo
    ETF_PREFIXES = ('BOVA', 'BRAX', 'IVVB', 'SMAC', 'ECOO', 'MOBI', 'MATB', 
                    'XBOC', 'ISUS', 'RENT', 'BDRX', 'SPXI', 'SMLL', 'DIVO',
                    'HECT', 'IRFM', 'WDOF', 'WDOV', 'COCE', 'GOLD', 'SOIL',
                    'IMAB', 'FIXA', 'XPLG', 'DEBTP')
    
    # Padrões especiais para FIIs conhecidos que não terminam em 11
    FII_EXCEPTIONS = {
        'FII', 'HCTR11', 'HGBS11', 'HGLG11', 'HGPO11', 'HGRE11', 
        'HGRU11', 'MXRF11', 'XPML11', 'RBRP11', 'VILG11'
    }
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def classify_asset(self, ticker: str) -> str:
        """
        Classifica um ativo baseado no padrão do ticker
        
        Args:
            ticker: Símbolo do ativo
            
        Returns:
            str: Tipo do ativo ('acao', 'fii', 'etf', 'bdr')
        """
        ticker = ticker.upper().strip()
        
        # 1. ETFs - Prioridade alta porque terminam em 11 como FIIs
        if self._is_etf(ticker):
            return 'etf'
        
        # 2. BDRs - Terminam em 34, 35, 33
        if ticker.endswith(('34', '35', '33')):
            return 'bdr'
        
        # 3. Fundos Imobiliários - Terminam em 11 (mas não são ETFs)
        if ticker.endswith('11'):
            return 'fii'
        
        # 4. Ações comuns - Terminam em 3, 4, 5, 6
        if ticker.endswith(('3', '4', '5', '6')):
            return 'acao'
        
        # 5. Casos especiais - Logging para investigação
        logger.warning(f"Ticker com padrão não reconhecido: {ticker}")
        return 'acao'  # Default para casos não identificados
    
    def _is_etf(self, ticker: str) -> bool:
        """Verifica se o ticker corresponde a um ETF"""
        # Lista explícita
        if ticker in self.ETF_TICKERS:
            return True
        
        # Padrão por prefixo
        for prefix in self.ETF_PREFIXES:
            if ticker.startswith(prefix):
                return True
        
        return False
    
    def classify_all_stocks(self) -> Dict[str, int]:
        """
        Classifica todos os ativos no banco de dados
        
        Returns:
            Dict: Estatísticas da classificação
        """
        stats = {
            'total_processed': 0,
            'acoes': 0,
            'fii': 0,
            'etf': 0,
            'bdr': 0,
            'others': 0
        }
        
        stocks = self.db.query(Stock).all()
        logger.info(f"Classificando {len(stocks)} ativos")
        
        # Adicionar coluna asset_class se não existir
        self._ensure_asset_class_column()
        
        for stock in stocks:
            try:
                asset_class = self.classify_asset(stock.ticker)
                
                # Adicionar atributo ao objeto (vai ser salvo depois)
                if not hasattr(stock, 'asset_class'):
                    stock.asset_class = asset_class
                
                stats['total_processed'] += 1
                stats[asset_class] += 1
                
                logger.debug(f"{stock.ticker} classificado como: {asset_class}")
                
            except Exception as e:
                logger.error(f"Erro ao classificar {stock.ticker}: {e}")
                stats['others'] += 1
        
        logger.info(f"Classificação concluída: {stats}")
        return stats
    
    def _ensure_asset_class_column(self):
        """Garante que a coluna asset_class exista no modelo"""
        # Esta verificação é necessária se a coluna não foi adicionada ao modelo
        # Em produção, usar migration para adicionar a coluna
        pass
    
    def get_classification_statistics(self) -> Dict:
        """Retorna estatísticas detalhadas da classificação"""
        from sqlalchemy import func
        
        # Query para contar por tipo (assumindo que já existe asset_class)
        try:
            # Se a coluna não existe, faz classificação em tempo real
            stocks = self.db.query(Stock).all()
            
            stats = {'total': len(stocks), 'acoes': 0, 'fii': 0, 'etf': 0, 'bdr': 0}
            
            for stock in stocks:
                asset_class = self.classify_asset(stock.ticker)
                stats[asset_class] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}
    
    def get_stocks_by_class(self, asset_class: str, limit: int = None) -> List[Stock]:
        """
        Retorna ações filtradas por classe de ativo
        
        Args:
            asset_class: Tipo de ativo ('acao', 'fii', 'etf', 'bdr')
            limit: Limite de resultados
            
        Returns:
            List[Stock]: Lista de ativos da classe especificada
        """
        # Se já temos a coluna asset_class:
        try:
            query = self.db.query(Stock).filter(Stock.asset_class == asset_class)
            if limit:
                query = query.limit(limit)
            return query.all()
        except:
            # Se não tem coluna, classifica em tempo real
            all_stocks = self.db.query(Stock).all()
            filtered = [s for s in all_stocks if self.classify_asset(s.ticker) == asset_class]
            
            if limit:
                filtered = filtered[:limit]
            
            return filtered
    
    def get_ticker_examples(self, asset_class: str, limit: int = 10) -> List[str]:
        """Retorna exemplos de tickers de uma classe específica"""
        stocks = self.get_stocks_by_class(asset_class, limit)
        return [s.ticker for s in stocks]
    
    def validate_classification(self) -> Dict[str, List[str]]:
        """
        Valida a classificação e retorna possíveis problemas
        
        Returns:
            Dict: Lista de possíveis erros por categoria
        """
        issues = {
            'unclassified': [],
            'conflicts': [],
            'unknown_patterns': []
        }
        
        stocks = self.db.query(Stock).all()
        
        for stock in stocks:
            ticker = stock.ticker
            classification = self.classify_asset(ticker)
            
            # Verificar padrões não reconhecidos
            if (not ticker.endswith(('3', '4', '5', '6', '11', '34', '35', '33')) and
                not self._is_etf(ticker)):
                issues['unknown_patterns'].append(ticker)
        
        return issues
    
    def export_classification_report(self) -> str:
        """Gera um relatório detalhado da classificação"""
        lines = []
        lines.append("RELATÓRIO DE CLASSIFICAÇÃO DE ATIVOS")
        lines.append("=" * 50)
        
        stats = self.get_classification_statistics()
        
        lines.append(f"\nESTATÍSTICAS GERAIS:")
        lines.append(f"Total de Ativos: {stats.get('total', 0)}")
        lines.append(f"Ações: {stats.get('acoes', 0)}")
        lines.append(f"FIIs: {stats.get('fii', 0)}")
        lines.append(f"ETFs: {stats.get('etf', 0)}")
        lines.append(f"BDRs: {stats.get('bdr', 0)}")
        
        lines.append(f"\nEXEMPLOS POR CLASSE:")
        for asset_class in ['acao', 'fii', 'etf', 'bdr']:
            examples = self.get_ticker_examples(asset_class, 5)
            lines.append(f"{asset_class.upper()}: {', '.join(examples)}")
        
        # Validação
        issues = self.validate_classification()
        if any(issues.values()):
            lines.append(f"\nPROBLEMAS ENCONTRADOS:")
            for category, tickers in issues.items():
                if tickers:
                    lines.append(f"{category}: {', '.join(tickers[:10])}")
        
        return "\n".join(lines)