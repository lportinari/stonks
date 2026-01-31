#!/usr/bin/env python3
"""
Script para testar o serviço de logos
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from services.logo_service import LogoService
from models.stock import Stock
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_logo_service():
    """Testa o serviço de logos para uma amostra de ações"""
    session = SessionLocal()
    
    try:
        logo_service = LogoService(session)
        
        # Testar com algumas ações conhecidas
        test_tickers = ['PETR4', 'VALE3', 'ITUB4', 'WEGE3', 'MGLU3']
        
        logger.info("TESTANDO SERVIÇO DE LOGOS")
        logger.info("="*50)
        
        for ticker in test_tickers:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                logger.warning(f"Ação {ticker} não encontrada")
                continue
            
            logger.info(f"\nAnalisando {ticker} ({stock.empresa}):")
            logger.info(f"  Logo atual: {stock.logo_url}")
            
            # Obter novo logo
            logo_url = logo_service.get_logo_url(ticker, force_refresh=True)
            
            if logo_url:
                logger.info(f"  => NOVO LOGO: {logo_url}")
                
                # Validar URL
                is_valid = logo_service.validate_logo_url(logo_url)
                logger.info(f"  => URL VÁLIDA: {'✅' if is_valid else '❌'}")
                
                if stock.logo_url != logo_url:
                    logger.info(f"  => LOGO DIFERENTE DO ATUAL")
                else:
                    logger.info(f"  => LOGO IGUAL AO ATUAL")
            else:
                logger.warning(f"  => NÃO FOI POSSÍVEL OBTER LOGO")
        
        # Estatísticas atuais
        stats = logo_service.get_logo_statistics()
        logger.info(f"\nESTATÍSTICAS ATUAIS:")
        logger.info(f"Total de ativos: {stats['total_stocks']}")
        logger.info(f"Com logo: {stats['with_logo']}")
        logger.info(f"Sem logo: {stats['without_logo']}")
        logger.info(f"Cobertura: {stats['coverage_percentage']:.1f}%")
        logger.info(f"Cache size: {stats['cache_size']}")
        
        # Testar atualização em lote (limitado para teste)
        logger.info(f"\nTESTANDO ATUALIZAÇÃO EM LOTE (limit 5):")
        update_stats = logo_service.update_logos_for_all_stocks(limit=5)
        logger.info(f"Estatísticas da atualização: {update_stats}")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    """Função principal"""
    test_logo_service()

if __name__ == "__main__":
    main()