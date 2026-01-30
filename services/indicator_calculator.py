import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging
from config import Config

logger = logging.getLogger(__name__)

class IndicatorCalculator:
    """Classe responsável por calcular indicadores e normalizar dados"""
    
    def __init__(self):
        self.indicator_limits = Config.INDICATOR_LIMITS
    
    def normalize_indicator(self, value: Optional[float], indicator_type: str) -> Optional[float]:
        """
        Normaliza um indicador para escala 0-1 usando min-max scaling
        
        Args:
            value: Valor do indicador
            indicator_type: Tipo do indicador (ex: 'dy', 'pl', 'pvp')
            
        Returns:
            float: Valor normalizado entre 0 e 1 ou None
        """
        if value is None:
            return None
            
        if indicator_type not in self.indicator_limits:
            logger.warning(f"Indicador {indicator_type} não configurado para normalização")
            return None
        
        limits = self.indicator_limits[indicator_type]
        min_val = limits['min']
        max_val = limits['max']
        
        # Para indicadores onde menor é melhor (como P/L, P/VP)
        if indicator_type in ['pl', 'pvp', 'psr', 'ev_ebit', 'ev_ebitda']:
            # Inverter a escala: menor valor = melhor = pontuação mais alta
            if value <= min_val:
                return 1.0
            elif value >= max_val:
                return 0.0
            else:
                return 1.0 - ((value - min_val) / (max_val - min_val))
        
        # Para indicadores onde maior é melhor (como DY, ROE, Margem)
        else:
            if value <= min_val:
                return 0.0
            elif value >= max_val:
                return 1.0
            else:
                return (value - min_val) / (max_val - min_val)
    
    def calculate_stock_score(self, stock_data: Dict, weights: Dict) -> Optional[float]:
        """
        Calcula a pontuação final de uma ação baseado nos indicadores e pesos
        
        Args:
            stock_data: Dicionário com dados da ação
            weights: Dicionário com pesos para cada indicador
            
        Returns:
            float: Pontuação final (0-100) ou None
        """
        try:
            score = 0.0
            total_weight = 0.0
            
            # Mapeamento dos indicadores para os campos no dicionário
            indicator_mapping = {
                'dy': 'div_yield',
                'pl': 'pl',
                'pvp': 'pvp',
                'roe': 'roe',
                'margem_liquida': 'margem_liquida',
                'roic': 'roic',
                'margem_ebit': 'margem_ebit',
                'liquidez_corr': 'liquidity'
            }
            
            for indicator, weight in weights.items():
                if weight <= 0:
                    continue
                    
                # Obter o valor do indicador
                field_name = indicator_mapping.get(indicator, indicator)
                value = stock_data.get(field_name)
                
                if value is not None:
                    # Normalizar o indicador
                    normalized = self.normalize_indicator(value, indicator)
                    
                    if normalized is not None:
                        score += normalized * weight
                        total_weight += weight
                    else:
                        logger.warning(f"Não foi possível normalizar {indicator} para {stock_data.get('ticker')}")
                else:
                    logger.debug(f"Indicador {indicator} não encontrado para {stock_data.get('ticker')}")
            
            # Normalizar pelo peso total para garantir escala 0-1
            if total_weight > 0:
                score = score / total_weight
                return score * 100  # Converter para escala 0-100
            else:
                logger.warning(f"Nenhum indicador válido encontrado para {stock_data.get('ticker')}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao calcular score para {stock_data.get('ticker')}: {e}")
            return None
    
    def calculate_batch_scores(self, stocks_data: List[Dict], weights: Dict) -> List[Dict]:
        """
        Calcula scores para um lote de ações
        
        Args:
            stocks_data: Lista com dados das ações
            weights: Pesos dos indicadores
            
        Returns:
            List[Dict]: Lista com dados atualizados incluindo scores
        """
        scored_stocks = []
        
        for stock in stocks_data:
            score = self.calculate_stock_score(stock, weights)
            stock_with_score = stock.copy()
            stock_with_score['score_final'] = score
            scored_stocks.append(stock_with_score)
        
        return scored_stocks
    
    def rank_stocks(self, stocks_data: List[Dict]) -> List[Dict]:
        """
        Ordena ações por score e adiciona posição no ranking
        
        Args:
            stocks_data: Lista com dados das ações (já com scores)
            
        Returns:
            List[Dict]: Lista ordenada com posições do ranking
        """
        # Filtrar apenas ações com score válido
        valid_stocks = [stock for stock in stocks_data if stock.get('score_final') is not None]
        
        # Ordenar por score (maior para menor)
        sorted_stocks = sorted(valid_stocks, key=lambda x: x['score_final'], reverse=True)
        
        # Adicionar posição no ranking
        for i, stock in enumerate(sorted_stocks, 1):
            stock['rank_posicao'] = i
        
        return sorted_stocks
    
    def get_top_stocks(self, stocks_data: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Retorna as N melhores ações
        
        Args:
            stocks_data: Lista com dados das ações ordenadas
            limit: Número de ações a retornar
            
        Returns:
            List[Dict]: Top N ações
        """
        return stocks_data[:limit]
    
    def filter_stocks_by_criteria(self, stocks_data: List[Dict], filters: Dict) -> List[Dict]:
        """
        Filtra ações baseado em critérios específicos
        
        Args:
            stocks_data: Lista com dados das ações
            filters: Dicionário com critérios de filtro
            
        Returns:
            List[Dict]: Lista filtrada de ações
        """
        filtered_stocks = stocks_data.copy()
        
        for field, criteria in filters.items():
            if isinstance(criteria, dict):
                # Filtro de range (min/max)
                min_val = criteria.get('min')
                max_val = criteria.get('max')
                
                filtered_stocks = [
                    stock for stock in filtered_stocks
                    if self._meets_criteria(stock.get(field), min_val, max_val)
                ]
            elif isinstance(criteria, list):
                # Filtro de lista de valores aceitos
                filtered_stocks = [
                    stock for stock in filtered_stocks
                    if stock.get(field) in criteria
                ]
            else:
                # Filtro de valor exato
                filtered_stocks = [
                    stock for stock in filtered_stocks
                    if stock.get(field) == criteria
                ]
        
        return filtered_stocks
    
    def _meets_criteria(self, value, min_val=None, max_val=None) -> bool:
        """Verifica se um valor atende aos critérios min/max"""
        if value is None:
            return False
        
        if min_val is not None and value < min_val:
            return False
        
        if max_val is not None and value > max_val:
            return False
        
        return True
    
    def calculate_sector_stats(self, stocks_data: List[Dict]) -> Dict[str, Dict]:
        """
        Calcula estatísticas por setor
        
        Args:
            stocks_data: Lista com dados das ações
            
        Returns:
            Dict: Estatísticas por setor
        """
        sector_stats = {}
        
        # Agrupar por setor
        sectors = {}
        for stock in stocks_data:
            setor = stock.get('setor', 'Não Classificado')
            if setor not in sectors:
                sectors[setor] = []
            sectors[setor].append(stock)
        
        # Calcular estatísticas para cada setor
        for setor, sector_stocks in sectors.items():
            valid_scores = [s['score_final'] for s in sector_stocks if s.get('score_final') is not None]
            
            if valid_scores:
                sector_stats[setor] = {
                    'count': len(sector_stocks),
                    'avg_score': np.mean(valid_scores),
                    'median_score': np.median(valid_scores),
                    'min_score': np.min(valid_scores),
                    'max_score': np.max(valid_scores),
                    'top_stock': max(sector_stocks, key=lambda x: x.get('score_final', 0))
                }
        
        return sector_stats