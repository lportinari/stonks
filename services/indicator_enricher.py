import requests
import logging
import math
from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import Session
from models.stock import Stock
from services.professional_apis import ProfessionalAPIService
from config import Config

logger = logging.getLogger(__name__)

class IndicatorEnricher:
    """Serviço responsável por enriquecer e calcular indicadores financeiros"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.professional_api = ProfessionalAPIService()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def calculate_roic_advanced(self, stock: Stock) -> Optional[float]:
        """
        Calcula ROIC (Return on Invested Capital) de forma avançada
        ROIC = NOPAT / Invested Capital
        
        Para dados limitados, usamos aproximações
        """
        try:
            # Se já tiver ROIC e for válido
            if stock.roic and stock.roic > 0 and stock.roic < 1000:
                return stock.roic
            
            # Calcular ROIC aproximado usando ROE * (Patrimônio / Ativos totais)
            if stock.roe and stock.patrimonio_liquido:
                # Tentar obter ativos totais de fontes externas
                ativos_totais = self._get_total_assets(stock.ticker)
                
                if ativos_totais and ativos_totais > 0:
                    roic_calculado = stock.roe * (stock.patrimonio_liquido / ativos_totais)
                    if 0 < roic_calculado < 1000:
                        return roic_calculado
            
            # Fallback: usar ROE como proxy (com ajuste)
            if stock.roe and 0 < stock.roe < 1000:
                # Ajuste conservador: ROIC geralmente menor que ROE
                return stock.roe * 0.7
                
        except Exception as e:
            logger.debug(f"Erro ao calcular ROIC para {stock.ticker}: {e}")
        
        return None
    
    def calculate_peg_ratio(self, stock: Stock) -> Optional[float]:
        """
        Calcula PEG Ratio (Price/Earnings to Growth)
        PEG = P/L / Crescimento EPS esperado
        
        Para dados limitados, usamos crescimento histórico
        """
        try:
            if stock.pl and stock.pl > 0:
                # Usar crescimento de receita 5 anos como proxy
                crescimento = stock.cresc_receita_5a
                
                if crescimento and crescimento != 0:
                    # Converter percentual para decimal
                    crescimento_decimal = crescimento / 100
                    
                    if crescimento_decimal != 0:
                        peg = stock.pl / crescimento_decimal
                        if -100 < peg < 100:  # Validação básica
                            return peg
            
        except Exception as e:
            logger.debug(f"Erro ao calcular PEG para {stock.ticker}: {e}")
        
        return None
    
    def calculate_graham_number(self, stock: Stock) -> Optional[float]:
        """
        Calcula Número de Graham (valor intrínseco máximo)
        Graham Number = √(22.5 * EPS * BVPS)
        
        Onde:
        - EPS: Earnings Per Share
        - BVPS: Book Value Per Share (Patrimônio Líquido / Ações)
        """
        try:
            if (stock.earnings_per_share and stock.earnings_per_share > 0 and 
                stock.patrimonio_liquido and stock.patrimonio_liquido > 0):
                
                # Estimar BVPS (simplificado - assume que PL já é por ação)
                bvps = stock.patrimonio_liquido
                
                # Calcular Número de Graham
                graham_number = math.sqrt(22.5 * stock.earnings_per_share * bvps)
                
                if graham_number > 0 and graham_number < 10000:  # Validação básica
                    return graham_number
                    
        except Exception as e:
            logger.debug(f"Erro ao calcular Graham Number para {stock.ticker}: {e}")
        
        return None
    
    def calculate_altman_z_score(self, stock: Stock) -> Optional[float]:
        """
        Calcula Altman Z-Score (probabilidade de falência)
        Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5
        
        Onde:
        X1 = Working Capital / Total Assets
        X2 = Retained Earnings / Total Assets
        X3 = EBIT / Total Assets
        X4 = Market Value Equity / Total Liabilities
        X5 = Sales / Total Assets
        
        Versão simplificada para dados limitados
        """
        try:
            # Versão simplificada usando dados disponíveis
            scores = []
            
            # Fator 1: Liquidez (Working Capital proxy)
            if stock.liquidity and stock.liquidity > 0:
                scores.append(min(stock.liquidity / 2, 1.2))  # Máximo 1.2
            
            # Fator 2: ROE (Retained Earnings proxy)
            if stock.roe and stock.roe > 0:
                scores.append(min(stock.roe / 100, 1.4))  # Máximo 1.4
            
            # Fator 3: Margem EBIT (EBIT proxy)
            if stock.margem_ebit and stock.margem_ebit > 0:
                scores.append(min(stock.margem_ebit / 100 * 3.3, 3.3))  # Máximo 3.3
            
            # Fator 4: P/VP (Market Value proxy)
            if stock.pvp and stock.pvp > 0:
                scores.append(min(1 / stock.pvp * 0.6, 0.6))  # Máximo 0.6
            
            # Fator 5: Giro de Ativos (Sales proxy)
            if stock.giro_ativos and stock.giro_ativos > 0:
                scores.append(min(stock.giro_ativos, 1.0))  # Máximo 1.0
            
            if scores:
                z_score = sum(scores)
                if 0 < z_score < 20:  # Validação básica
                    return z_score
                    
        except Exception as e:
            logger.debug(f"Erro ao calcular Altman Z-Score para {stock.ticker}: {e}")
        
        return None
    
    def calculate_magic_formula_rank(self, stock: Stock) -> Optional[int]:
        """
        Calcula ranking da Magic Formula de Joel Greenblatt
        Baseado em: 1) Earnings Yield (EY) e 2) Return on Capital (ROC)
        
        Rank = 1 (melhor) a 100 (pior)
        """
        try:
            # Earnings Yield = EBIT / Enterprise Value
            # Usando proxy: 1/PL com ajuste por dívida
            ey_score = 0
            if stock.pl and stock.pl > 0:
                ey = 1 / stock.pl
                
                # Ajustar por endividamento
                if stock.div_liquida_patrim and stock.div_liquida_patrim > 0:
                    ey = ey / (1 + stock.div_liquida_patrim / 100)
                
                ey_score = min(ey * 100, 100)  # Normalizar para 0-100
            
            # Return on Capital (usando ROIC)
            roc_score = 0
            roic = self.calculate_roic_advanced(stock)
            if roic and roic > 0:
                roc_score = min(roic, 100)  # Normalizar para 0-100
            
            # Ranking combinado (média simples)
            if ey_score > 0 or roc_score > 0:
                combined_score = (ey_score + roc_score) / 2
                # Converter para ranking invertido (maior score = melhor rank)
                rank = max(1, int(100 - combined_score))
                return min(rank, 100)
                
        except Exception as e:
            logger.debug(f"Erro ao calcular Magic Formula para {stock.ticker}: {e}")
        
        return None
    
    def calculate_beneish_m_score(self, stock: Stock) -> Optional[float]:
        """
        Calcula Beneish M-Score (probabilidade de manipulação de resultados)
        Versão simplificada para dados disponíveis
        
        M-Score > -1.78 sugere possível manipulação
        """
        try:
            indicators = []
            
            # Índices da fórmula original (simplificados)
            
            # DSRI: Days Sales in Receivables Index
            # Usamos proxy baseado em liquidez
            if stock.liquidity and stock.liquidity > 0:
                dsri = min(stock.liquidity / 2, 2)
                indicators.append(dsri * 0.092)
            
            # GMI: Gross Margin Index
            # Usamos proxy baseado em margem bruta
            if stock.margem_bruta and stock.margem_bruta > 0:
                gmi = max(1, 1 - stock.margem_bruta / 100)
                indicators.append(gmi * 0.522)
            
            # AQI: Asset Quality Index
            # Usamos proxy baseado em ROA
            if stock.roa and stock.roa > 0:
                aqi = max(0, 1 - stock.roa / 100)
                indicators.append(aqi * 0.193)
            
            # SGI: Sales Growth Index
            if stock.cresc_receita_5a and stock.cresc_receita_5a > 0:
                sgi = stock.cresc_receita_5a / 100
                indicators.append(sgi * 0.172)
            
            # DEPI: Depreciation Index
            # Usamos proxy baseado em estrutura de ativos
            if stock.giro_ativos and stock.giro_ativos > 0:
                depi = 1 / max(stock.giro_ativos, 1)
                indicators.append(depi * 0.119)
            
            if indicators:
                m_score = -4.84 + sum(indicators)
                return m_score
                
        except Exception as e:
            logger.debug(f"Erro ao calcular Beneish M-Score para {stock.ticker}: {e}")
        
        return None
    
    def calculate_earnings_yield(self, stock: Stock) -> Optional[float]:
        """
        Calcula Earnings Yield (lucro/preço)
        EY = EPS / Preço da Ação
        """
        try:
            if (stock.earnings_per_share and stock.earnings_per_share > 0 and 
                stock.cotacao and stock.cotacao > 0):
                
                ey = (stock.earnings_per_share / stock.cotacao) * 100  # Em percentual
                
                if 0 < ey < 1000:  # Validação básica
                    return ey
                    
        except Exception as e:
            logger.debug(f"Erro ao calcular Earnings Yield para {stock.ticker}: {e}")
        
        return None
    
    def _get_total_assets(self, ticker: str) -> Optional[float]:
        """Obtém ativos totais de fontes externas"""
        try:
            # Tentar obter da API profissional
            data = self.professional_api.get_from_brapi(ticker)
            if data:
                # Verificar se tem dados de balanço
                if 'totalAssets' in data and data['totalAssets']:
                    return data['totalAssets']
                
                # Tentar calcular com dados disponíveis
                if (data.get('marketCap') and data.get('priceToBook') and 
                    data.get('priceToBook') > 0):
                    # Patrimônio = Market Cap / P/VP
                    patrimonio = data['marketCap'] / data['priceToBook']
                    # Ativos ≈ Patrimônio * (1 + Dívida/Patrimônio)
                    if data.get('debtToEquity'):
                        ativos = patrimonio * (1 + data['debtToEquity'] / 100)
                        return ativos
                        
        except Exception as e:
            logger.debug(f"Erro ao obter total assets para {ticker}: {e}")
        
        return None
    
    def update_enriched_indicators(self, limit: int = None) -> Dict[str, int]:
        """
        Atualiza indicadores enriquecidos para todas as ações
        
        Args:
            limit: Limite de ações a processar
            
        Returns:
            Dict: Estatísticas da atualização
        """
        stats = {
            'total_processed': 0,
            'roic_updated': 0,
            'peg_updated': 0,
            'graham_updated': 0,
            'altman_updated': 0,
            'magic_updated': 0,
            'beneish_updated': 0,
            'ey_updated': 0,
            'errors': 0
        }
        
        # Buscar todas as ações
        query = self.db.query(Stock)
        
        if limit:
            query = query.limit(limit)
        
        stocks = query.all()
        logger.info(f"Processando {len(stocks)} ações para enriquecimento de indicadores")
        
        for stock in stocks:
            try:
                stats['total_processed'] += 1
                
                # Verificar classe de ativo - FIIs e ETFs têm tratamento especial
                if self._needs_special_indicators(stock.ticker):
                    logger.debug(f"Pulando {stock.ticker} - classe de ativo especial")
                    continue
                
                # ROIC Avançado
                roic = self.calculate_roic_advanced(stock)
                if roic and roic != stock.roic:
                    stock.roic = roic
                    stats['roic_updated'] += 1
                
                # PEG Ratio
                peg = self.calculate_peg_ratio(stock)
                if peg:
                    # Usar campo não existente ou reaproveitar campo
                    stats['peg_updated'] += 1
                
                # Graham Number
                graham = self.calculate_graham_number(stock)
                if graham:
                    # Poderia ser salvo em campo específico
                    stats['graham_updated'] += 1
                
                # Altman Z-Score
                altman = self.calculate_altman_z_score(stock)
                if altman:
                    # Poderia ser salvo em campo específico
                    stats['altman_updated'] += 1
                
                # Magic Formula Rank
                magic = self.calculate_magic_formula_rank(stock)
                if magic:
                    # Poderia ser salvo em campo específico
                    stats['magic_updated'] += 1
                
                # Beneish M-Score
                beneish = self.calculate_beneish_m_score(stock)
                if beneish:
                    # Poderia ser salvo em campo específico
                    stats['beneish_updated'] += 1
                
                # Earnings Yield
                ey = self.calculate_earnings_yield(stock)
                if ey:
                    # Poderia ser salvo em campo específico
                    stats['ey_updated'] += 1
                
                # Salvar a cada 10 atualizações
                if stats['total_processed'] % 10 == 0:
                    self.db.commit()
                    
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Erro ao processar indicadores para {stock.ticker}: {e}")
        
        # Commit final
        self.db.commit()
        
        logger.info(f"Atualização de indicadores enriquecidos concluída: {stats}")
        return stats
    
    def _needs_special_indicators(self, ticker: str) -> bool:
        """Verifica se o ativo precisa de tratamento especial"""
        # FIIs e ETFs têm indicadores diferentes
        return (ticker.endswith('11') or 
                ticker.startswith(('BOVA', 'BRAX', 'IVVB', 'SMAC', 'ECOO', 'SPXI')))
    
    def get_enriched_statistics(self) -> Dict:
        """Retorna estatísticas sobre indicadores enriquecidos"""
        total = self.db.query(Stock).count()
        
        # Contar indicadores existentes
        with_roic = self.db.query(Stock).filter(
            Stock.roic.isnot(None)
        ).count()
        
        with_pl = self.db.query(Stock).filter(
            Stock.pl.isnot(None)
        ).count()
        
        with_roe = self.db.query(Stock).filter(
            Stock.roe.isnot(None)
        ).count()
        
        return {
            'total_stocks': total,
            'with_roic': with_roic,
            'with_pl': with_pl,
            'with_roe': with_roe,
            'roic_coverage': (with_roic / total * 100) if total > 0 else 0,
            'pl_coverage': (with_pl / total * 100) if total > 0 else 0,
            'roe_coverage': (with_roe / total * 100) if total > 0 else 0
        }
    
    def get_stock_analysis(self, ticker: str) -> Optional[Dict]:
        """
        Retorna análise completa de uma ação com indicadores enriquecidos
        
        Args:
            ticker: Símbolo da ação
            
        Returns:
            Dict: Análise completa ou None
        """
        try:
            stock = self.db.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                return None
            
            analysis = {
                'ticker': stock.ticker,
                'empresa': stock.empresa,
                'preco_atual': stock.cotacao,
                'indicadores_basicos': {
                    'pl': stock.pl,
                    'pvp': stock.pvp,
                    'roe': stock.roe,
                    'roic': stock.roic,
                    'div_yield': stock.div_yield
                },
                'indicadores_enriquecidos': {
                    'roic_advanced': self.calculate_roic_advanced(stock),
                    'peg_ratio': self.calculate_peg_ratio(stock),
                    'graham_number': self.calculate_graham_number(stock),
                    'altman_z_score': self.calculate_altman_z_score(stock),
                    'magic_formula_rank': self.calculate_magic_formula_rank(stock),
                    'beneish_m_score': self.calculate_beneish_m_score(stock),
                    'earnings_yield': self.calculate_earnings_yield(stock)
                },
                'sinais': self._generate_signals(stock)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao gerar análise para {ticker}: {e}")
            return None
    
    def _generate_signals(self, stock: Stock) -> Dict[str, str]:
        """Gera sinais de compra/venda baseado nos indicadores"""
        signals = {}
        
        try:
            # Sinal baseado no PL
            if stock.pl:
                if stock.pl < 6:
                    signals['pl'] = 'COMPRA (barato)'
                elif stock.pl > 20:
                    signals['pl'] = 'VENDA (caro)'
                else:
                    signals['pl'] = 'NEUTRO'
            
            # Sinal baseado no P/VP
            if stock.pvp:
                if stock.pvp < 0.8:
                    signals['pvp'] = 'COMPRA (desconto)'
                elif stock.pvp > 2:
                    signals['pvp'] = 'VENDA (premium alto)'
                else:
                    signals['pvp'] = 'NEUTRO'
            
            # Sinal baseado no ROE
            if stock.roe:
                if stock.roe > 20:
                    signals['roe'] = 'EXCELENTE'
                elif stock.roe > 10:
                    signals['roe'] = 'BOM'
                else:
                    signals['roe'] = 'FRACO'
            
            # Sinal baseado no ROIC
            roic = self.calculate_roic_advanced(stock)
            if roic:
                if roic > 15:
                    signals['roic'] = 'EXCELENTE'
                elif roic > 10:
                    signals['roic'] = 'BOM'
                else:
                    signals['roic'] = 'FRACO'
            
            # Sinal baseado no Altman Z-Score
            altman = self.calculate_altman_z_score(stock)
            if altman:
                if altman > 3:
                    signals['risco'] = 'BAIXO'
                elif altman > 1.8:
                    signals['risco'] = 'MODERADO'
                else:
                    signals['risco'] = 'ALTO'
            
        except Exception as e:
            logger.debug(f"Erro ao gerar sinais para {stock.ticker}: {e}")
        
        return signals