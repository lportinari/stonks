#!/usr/bin/env python3
"""
Script para testar o serviço de cálculo de PL
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from services.pl_calculator import PLCalculator
from models.stock import Stock
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pl_calculation():
    """Testa o cálculo de PL para uma amostra de ações"""
    session = SessionLocal()
    
    try:
        calculator = PLCalculator(session)
        
        # Testar com algumas ações conhecidas
        test_tickers = ['VALE3', 'PETR4', 'ITUB4', 'WEGE3', 'MGLU3']
        
        logger.info("TESTANDO CÁLCULO DE PL")
        logger.info("="*50)
        
        for ticker in test_tickers:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                logger.warning(f"Ação {ticker} não encontrada")
                continue
            
            logger.info(f"\nAnalisando {ticker} ({stock.empresa}):")
            logger.info(f"  PL atual: {stock.pl}")
            logger.info(f"  Cotação: {stock.cotacao}")
            logger.info(f"  Earnings per Share: {stock.earnings_per_share}")
            logger.info(f"  Price Earnings (BrAPI): {stock.price_earnings}")
            
            # Calcular novo PL
            new_pl = calculator.calculate_pl_for_stock(stock)
            
            if new_pl:
                logger.info(f"  => NOVO PL CALCULADO: {new_pl:.2f}")
                
                # Verificar se houve mudança significativa
                if stock.pl:
                    diff_pct = abs((new_pl - stock.pl) / stock.pl * 100)
                    if diff_pct > 10:
                        logger.info(f"  => MUDANÇA SIGNIFICATIVA: {diff_pct:.1f}%")
                else:
                    logger.info(f"  => PL ANTES INEXISTENTE")
            else:
                logger.warning(f"  => NÃO FOI POSSÍVEL CALCULAR PL")
        
        # Estatísticas atuais
        stats = calculator.get_pl_statistics()
        logger.info(f"\nESTATÍSTICAS ATUAIS:")
        logger.info(f"Total de ativos: {stats['total_stocks']}")
        logger.info(f"Com PL: {stats['with_pl']}")
        logger.info(f"Sem PL: {stats['without_pl']}")
        logger.info(f"Cobertura: {stats['coverage_percentage']:.1f}%")
        
        # Testar atualização em lote (limitado para teste)
        logger.info(f"\nTESTANDO ATUALIZAÇÃO EM LOTE (limit 10):")
        update_stats = calculator.update_pl_for_all_stocks(limit=10)
        logger.info(f"Estatísticas da atualização: {update_stats}")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    """Função principal"""
    test_pl_calculation()

if __name__ == "__main__":
    main()