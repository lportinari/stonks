#!/usr/bin/env python3
"""
Script para testar o serviço de indicadores enriquecidos
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from services.indicator_enricher import IndicatorEnricher
from models.stock import Stock
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_indicator_enricher():
    """Testa o serviço de indicadores enriquecidos para uma amostra de ações"""
    session = SessionLocal()
    
    try:
        enricher = IndicatorEnricher(session)
        
        # Testar com algumas ações conhecidas
        test_tickers = ['PETR4', 'VALE3', 'ITUB4', 'WEGE3', 'MGLU3']
        
        logger.info("TESTANDO SERVIÇO DE INDICADORES ENRIQUECIDOS")
        logger.info("="*60)
        
        for ticker in test_tickers:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                logger.warning(f"Ação {ticker} não encontrada")
                continue
            
            logger.info(f"\nAnalisando {ticker} ({stock.empresa}):")
            logger.info(f"  Preço: R$ {stock.cotacao}")
            logger.info(f"  PL: {stock.pl}")
            logger.info(f"  P/VP: {stock.pvp}")
            logger.info(f"  ROE: {stock.roe}%")
            
            # Testar indicadores enriquecidos
            roic = enricher.calculate_roic_advanced(stock)
            if roic:
                logger.info(f"  ROIC Avançado: {roic:.2f}%")
            
            peg = enricher.calculate_peg_ratio(stock)
            if peg:
                logger.info(f"  PEG Ratio: {peg:.2f}")
            
            graham = enricher.calculate_graham_number(stock)
            if graham:
                logger.info(f"  Número de Graham: R$ {graham:.2f}")
                margem_seguranca = ((graham - stock.cotacao) / stock.cotacao * 100) if stock.cotacao else 0
                logger.info(f"  Margem de Segurança: {margem_seguranca:.1f}%")
            
            altman = enricher.calculate_altman_z_score(stock)
            if altman:
                risco = "BAIXO" if altman > 3 else "MODERADO" if altman > 1.8 else "ALTO"
                logger.info(f"  Altman Z-Score: {altman:.2f} (Risco: {risco})")
            
            magic = enricher.calculate_magic_formula_rank(stock)
            if magic:
                classificacao = "EXCELENTE" if magic <= 10 else "BOM" if magic <= 30 else "REGULAR"
                logger.info(f"  Magic Formula Rank: {magic}/100 ({classificacao})")
            
            beneish = enricher.calculate_beneish_m_score(stock)
            if beneish:
                manipulacao = "POSSÍVEL" if beneish > -1.78 else "POUCO PROVÁVEL"
                logger.info(f"  Beneish M-Score: {beneish:.2f} ({manipulacao})")
            
            ey = enricher.calculate_earnings_yield(stock)
            if ey:
                logger.info(f"  Earnings Yield: {ey:.2f}%")
            
            # Análise completa
            analysis = enricher.get_stock_analysis(ticker)
            if analysis and analysis.get('sinais'):
                logger.info(f"  Sinais: {analysis['sinais']}")
        
        # Estatísticas atuais
        stats = enricher.get_enriched_statistics()
        logger.info(f"\nESTATÍSTICAS ATUAIS:")
        logger.info(f"Total de ativos: {stats['total_stocks']}")
        logger.info(f"Com ROIC: {stats['with_roic']} ({stats['roic_coverage']:.1f}%)")
        logger.info(f"Com PL: {stats['with_pl']} ({stats['pl_coverage']:.1f}%)")
        logger.info(f"Com ROE: {stats['with_roe']} ({stats['roe_coverage']:.1f}%)")
        
        # Testar atualização em lote (limitado para teste)
        logger.info(f"\nTESTANDO ATUALIZAÇÃO EM LOTE (limit 5):")
        update_stats = enricher.update_enriched_indicators(limit=5)
        logger.info(f"Estatísticas da atualização: {update_stats}")
        
        # Análise detalhada de uma ação
        logger.info(f"\nANÁLISE DETALHADA - PETR4:")
        detailed_analysis = enricher.get_stock_analysis('PETR4')
        if detailed_analysis:
            logger.info(f"Empresa: {detailed_analysis['empresa']}")
            logger.info(f"Preço Atual: R$ {detailed_analysis['preco_atual']}")
            
            logger.info("\nIndicadores Básicos:")
            for key, value in detailed_analysis['indicadores_basicos'].items():
                if value is not None:
                    logger.info(f"  {key.upper()}: {value}")
            
            logger.info("\nIndicadores Enriquecidos:")
            for key, value in detailed_analysis['indicadores_enriquecidos'].items():
                if value is not None:
                    logger.info(f"  {key.replace('_', ' ').title()}: {value}")
            
            logger.info("\nSinais de Análise:")
            for key, value in detailed_analysis['sinais'].items():
                logger.info(f"  {key.upper()}: {value}")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    """Função principal"""
    test_indicator_enricher()

if __name__ == "__main__":
    main()