from typing import Dict, List, Optional
import logging
from sqlalchemy.orm import Session
from models.stock import Stock
from models.database import SessionLocal
from .indicator_calculator import IndicatorCalculator
from config import Config

logger = logging.getLogger(__name__)

class RankingService:
    """Classe responsável por gerenciar o sistema de ranking de ações"""
    
    def __init__(self):
        self.calculator = IndicatorCalculator()
        self.default_weights = Config.DEFAULT_WEIGHTS.copy()
    
    def get_current_ranking(self, limit: int = 50, sector_filter: Optional[str] = None, 
                          page: int = 1, per_page: int = 50) -> List[Stock]:
        """
        Obtém o ranking atual de ações com paginação
        
        Args:
            limit: Número máximo de ações a retornar (legado)
            sector_filter: Filtrar por setor específico
            page: Página atual
            per_page: Itens por página
            
        Returns:
            List[Stock]: Lista de ações ordenadas por ranking
        """
        with SessionLocal() as db:
            # Primeiro tenta com score_final calculado
            query_with_score = db.query(Stock).filter(Stock.score_final.isnot(None))
            
            if sector_filter:
                query_with_score = query_with_score.filter(Stock.setor == sector_filter)
            
            # Aplicar paginação real
            offset = (page - 1) * per_page
            stocks_with_score = query_with_score.order_by(Stock.score_final.desc()).offset(offset).limit(per_page).all()
            
            # Se não tiver suficientes com score, complementa com ações sem score
            if len(stocks_with_score) < per_page:
                remaining = per_page - len(stocks_with_score)
                ticker_exclude = [s.ticker for s in stocks_with_score]
                
                query_without_score = db.query(Stock).filter(
                    Stock.ticker.notin_(ticker_exclude),
                    Stock.score_final.is_(None)  # Apenas sem score
                )
                
                if sector_filter:
                    query_without_score = query_without_score.filter(Stock.setor == sector_filter)
                
                # Calcular offset correto para ações sem score
                # Se temos 18 ações com score e estamos na página 2 (offset=50)
                # então precisamos pular as primeiras 32 ações sem score da página 1
                # mais as 50 ações sem score da página 2 atual = 82 total
                if len(stocks_with_score) == 0:
                    # Se não há ações com score nesta página, o offset é ajustado
                    score_stocks_in_previous_pages = min(18, offset)  # 18 ações com score no total
                    without_score_offset = offset - score_stocks_in_previous_pages
                else:
                    without_score_offset = offset
                
                # Ordenar por cotacao (maior primeiro) para as sem score
                # E aplicar paginação para continuar de onde parou!
                stocks_without_score = query_without_score.filter(
                    Stock.cotacao.isnot(None)
                ).filter(
                    Stock.cotacao > 0
                ).order_by(Stock.cotacao.desc()).offset(without_score_offset).limit(remaining).all()
                
                # Garantir que todas as ações tenham valores padrão para evitar erros no template
                for stock in stocks_without_score:
                    if stock.score_final is None:
                        stock.score_final = 0
                    if stock.rank_posicao is None:
                        stock.rank_posicao = 999999  # Valor alto para ficar no final
                    # Garantir que campos numéricos não sejam None
                    if stock.cotacao is None:
                        stock.cotacao = 0
                    if stock.div_yield is None:
                        stock.div_yield = 0
                    if stock.pl is None:
                        stock.pl = 0
                    if stock.pvp is None:
                        stock.pvp = 0
                    if stock.roe is None:
                        stock.roe = 0
                    if stock.margem_liquida is None:
                        stock.margem_liquida = 0
                
                return stocks_with_score + stocks_without_score
            
            return stocks_with_score
    
    def get_top_stocks(self, limit: int = 10) -> List[Stock]:
        """
        Retorna as top N ações do ranking
        
        Args:
            limit: Número de ações a retornar
            
        Returns:
            List[Stock]: Top ações
        """
        return self.get_current_ranking(limit=limit)
    
    def get_stock_by_ticker(self, ticker: str) -> Optional[Stock]:
        """
        Busca uma ação pelo ticker
        
        Args:
            ticker: Ticker da ação
            
        Returns:
            Stock: Objeto da ação ou None
        """
        with SessionLocal() as db:
            return db.query(Stock).filter(Stock.ticker == ticker).first()
    
    def update_ranking(self, weights: Optional[Dict] = None) -> int:
        """
        Atualiza o ranking de todas as ações no banco
        
        Args:
            weights: Pesos customizados (usa padrão se None)
            
        Returns:
            int: Número de ações atualizadas
        """
        if weights is None:
            weights = self.default_weights
        
        with SessionLocal() as db:
            # Buscar todas as ações
            stocks = db.query(Stock).all()
            
            updated_count = 0
            for stock in stocks:
                # Converter para dicionário para cálculo
                stock_dict = stock.to_dict()
                
                # Calcular novo score
                new_score = self.calculator.calculate_stock_score(stock_dict, weights)
                
                if new_score is not None:
                    stock.score_final = new_score
                    updated_count += 1
            
            # Commit das alterações
            db.commit()
            
            # Atualizar posições do ranking
            self._update_ranking_positions(db)
            
            logger.info(f"Ranking atualizado: {updated_count} ações processadas")
            return updated_count
    
    def _update_ranking_positions(self, db: Session):
        """Atualiza as posições no ranking baseado nos scores"""
        stocks = db.query(Stock).filter(Stock.score_final.isnot(None)).order_by(Stock.score_final.desc()).all()
        
        for i, stock in enumerate(stocks, 1):
            stock.rank_posicao = i
        
        db.commit()
    
    def get_sector_ranking(self, sector: str, limit: int = 20) -> List[Stock]:
        """
        Obtém ranking de ações de um setor específico
        
        Args:
            sector: Nome do setor
            limit: Número máximo de ações
            
        Returns:
            List[Stock]: Ações do setor ordenadas
        """
        return self.get_current_ranking(limit=limit, sector_filter=sector)
    
    def get_available_sectors(self) -> List[str]:
        """
        Obtém lista de setores disponíveis no banco
        
        Returns:
            List[str]: Lista de setores
        """
        with SessionLocal() as db:
            sectors = db.query(Stock.setor).distinct().filter(Stock.setor.isnot(None)).all()
            return [sector[0] for sector in sectors if sector[0]]
    
    def filter_stocks(self, 
                     min_dy: Optional[float] = None,
                     max_pl: Optional[float] = None,
                     max_pvp: Optional[float] = None,
                     min_roe: Optional[float] = None,
                     sector: Optional[str] = None,
                     limit: int = 50) -> List[Stock]:
        """
        Filtra ações baseado em critérios específicos
        
        Args:
            min_dy: Dividend Yield mínimo
            max_pl: P/L máximo
            max_pvp: P/VP máximo
            min_roe: ROE mínimo
            sector: Filtro por setor
            limit: Limite de resultados
            
        Returns:
            List[Stock]: Ações filtradas
        """
        with SessionLocal() as db:
            query = db.query(Stock).filter(Stock.score_final.isnot(None))
            
            if min_dy is not None:
                query = query.filter(Stock.div_yield >= min_dy)
            
            if max_pl is not None:
                query = query.filter(Stock.pl <= max_pl)
            
            if max_pvp is not None:
                query = query.filter(Stock.pvp <= max_pvp)
            
            if min_roe is not None:
                query = query.filter(Stock.roe >= min_roe)
            
            if sector:
                query = query.filter(Stock.setor == sector)
            
            return query.order_by(Stock.score_final.desc()).limit(limit).all()
    
    def get_ranking_statistics(self) -> Dict:
        """
        Obtém estatísticas do ranking atual
        
        Returns:
            Dict: Estatísticas do ranking
        """
        with SessionLocal() as db:
            # Contar todas as ações com preço (não apenas com score)
            total_stocks = db.query(Stock).filter(
                Stock.cotacao.isnot(None)
            ).filter(
                Stock.cotacao > 0
            ).count()
            
            if total_stocks == 0:
                return {
                    'total_stocks': 0,
                    'avg_score': 0,
                    'median_score': 0,
                    'top_score': 0,
                    'sectors': []
                }
            
            # Obter scores para estatísticas (apenas ações com score)
            stocks_with_score = db.query(Stock).filter(Stock.score_final.isnot(None)).all()
            
            if not stocks_with_score:
                # Se não há ações com score, retornar estatísticas básicas
                all_stocks = db.query(Stock).filter(
                    Stock.cotacao.isnot(None)
                ).filter(
                    Stock.cotacao > 0
                ).all()
                
                sectors = {}
                for stock in all_stocks:
                    sector = stock.setor or 'Não Classificado'
                    sectors[sector] = sectors.get(sector, 0) + 1
                
                sector_stats = [{'name': k, 'count': v} for k, v in sectors.items()]
                
                return {
                    'total_stocks': total_stocks,
                    'avg_score': 0,
                    'median_score': 0,
                    'top_score': 0,
                    'sectors': sector_stats[:10]
                }
            
            scores = [stock.score_final for stock in stocks_with_score]
            
            # Estatísticas básicas
            stats = {
                'total_stocks': total_stocks,  # Todas as ações com preço
                'avg_score': sum(scores) / len(scores),
                'median_score': sorted(scores)[len(scores) // 2],
                'top_score': max(scores),
                'bottom_score': min(scores)
            }
            
            # Estatísticas por setor (todas as ações com preço)
            all_stocks = db.query(Stock).filter(
                Stock.cotacao.isnot(None)
            ).filter(
                Stock.cotacao > 0
            ).all()
            
            sectors = {}
            for stock in all_stocks:
                sector = stock.setor or 'Não Classificado'
                if sector not in sectors:
                    sectors[sector] = []
                sectors[sector].append(stock.score_final or 0)
            
            sector_stats = []
            for sector, sector_scores in sectors.items():
                sector_stats.append({
                    'name': sector,
                    'count': len(sector_scores),
                    'avg_score': sum(sector_scores) / len(sector_scores) if sector_scores else 0,
                    'top_score': max(sector_scores) if sector_scores else 0
                })
            
            # Ordenar por média de score
            sector_stats.sort(key=lambda x: x['avg_score'], reverse=True)
            stats['sectors'] = sector_stats[:10]  # Top 10 setores
            
            return stats
    
    def compare_stocks(self, tickers: List[str]) -> List[Dict]:
        """
        Compara múltiplas ações lado a lado
        
        Args:
            tickers: Lista de tickers para comparar
            
        Returns:
            List[Dict]: Dados comparativos das ações
        """
        comparison_data = []
        
        for ticker in tickers:
            stock = self.get_stock_by_ticker(ticker)
            if stock:
                stock_dict = stock.to_dict()
                comparison_data.append(stock_dict)
        
        # Ordenar por score
        comparison_data.sort(key=lambda x: x.get('score_final', 0), reverse=True)
        return comparison_data
    
    def save_custom_weights(self, weights: Dict, name: str) -> bool:
        """
        Salva configuração de pesos customizada (implementação futura)
        
        Args:
            weights: Dicionário de pesos
            name: Nome da configuração
            
        Returns:
            bool: True se salvo com sucesso
        """
        # TODO: Implementar salvamento de configurações customizadas
        # Poderia ser em uma tabela separada no banco
        logger.info(f"Configuração '{name}' salva (implementação pendente)")
        return True