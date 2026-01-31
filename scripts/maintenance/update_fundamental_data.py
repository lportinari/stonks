#!/usr/bin/env python3
"""
Script para atualizar dados fundamentalistas dos ativos usando Fundamentus
Isso vai preencher P/L, ROE, P/VP, DY, etc. que estão faltando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
from services.fundamentus_scraper import FundamentusScraper
from models.database import SessionLocal
from models.stock import Stock

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Função principal para atualizar dados fundamentalistas"""
    try:
        logger.info("Iniciando atualização de dados fundamentalistas...")
        
        # Inicializar scraper
        scraper = FundamentusScraper()
        
        # Testar conexão
        if not scraper.test_connection():
            logger.error("Não foi possível conectar ao Fundamentus")
            return 1
        
        # Buscar dados do Fundamentus
        logger.info("Buscando dados no Fundamentus...")
        fundamentus_data = scraper.get_stocks_data()
        
        if not fundamentus_data:
            logger.error("Não foi possível obter dados do Fundamentus")
            return 1
        
        logger.info(f"Obtidos dados de {len(fundamentus_data)} ativos do Fundamentus")
        
        # Atualizar banco de dados
        with SessionLocal() as db:
            updated_count = 0
            created_count = 0
            
            for stock_data in fundamentus_data:
                ticker = stock_data['ticker']
                
                # Buscar ativo existente
                existing_stock = db.query(Stock).filter(Stock.ticker == ticker).first()
                
                if existing_stock:
                    # Atualizar dados fundamentalistas
                    updated = False
                    
                    if stock_data.get('pl') is not None and existing_stock.pl is None:
                        existing_stock.pl = stock_data['pl']
                        updated = True
                    
                    if stock_data.get('roe') is not None and existing_stock.roe is None:
                        existing_stock.roe = stock_data['roe']
                        updated = True
                    
                    if stock_data.get('pvp') is not None and existing_stock.pvp is None:
                        existing_stock.pvp = stock_data['pvp']
                        updated = True
                    
                    if stock_data.get('div_yield') is not None and existing_stock.div_yield is None:
                        existing_stock.div_yield = stock_data['div_yield']
                        updated = True
                    
                    if stock_data.get('mrg_liq') is not None and existing_stock.margem_liquida is None:
                        existing_stock.margem_liquida = stock_data['mrg_liq']
                        updated = True
                    
                    if stock_data.get('roic') is not None and existing_stock.roic is None:
                        existing_stock.roic = stock_data['roic']
                        updated = True
                    
                    if stock_data.get('psr') is not None and existing_stock.psr is None:
                        existing_stock.psr = stock_data['psr']
                        updated = True
                    
                    if stock_data.get('ev_ebit') is not None and existing_stock.ev_ebit is None:
                        existing_stock.ev_ebit = stock_data['ev_ebit']
                        updated = True
                    
                    if stock_data.get('ev_ebitda') is not None and existing_stock.ev_ebitda is None:
                        existing_stock.ev_ebitda = stock_data['ev_ebitda']
                        updated = True
                    
                    if stock_data.get('liquidez_corr') is not None and existing_stock.liquidity is None:
                        existing_stock.liquidity = stock_data['liquidez_corr']
                        updated = True
                    
                    if stock_data.get('setor') and existing_stock.setor is None:
                        existing_stock.setor = stock_data['setor']
                        updated = True
                    
                    if stock_data.get('subsetor') and existing_stock.subsetor is None:
                        existing_stock.subsetor = stock_data['subsetor']
                        updated = True
                    
                    if updated:
                        updated_count += 1
                        logger.info(f"Atualizado {ticker}: P/L={existing_stock.pl}, ROE={existing_stock.roe}, DY={existing_stock.div_yield}")
                
                else:
                    # Criar novo ativo (caso não exista)
                    new_stock = Stock(
                        ticker=stock_data['ticker'],
                        empresa=stock_data['empresa'],
                        setor=stock_data.get('setor'),
                        subsetor=stock_data.get('subsetor'),
                        cotacao=stock_data.get('cotacao'),
                        pl=stock_data.get('pl'),
                        pvp=stock_data.get('pvp'),
                        psr=stock_data.get('psr'),
                        div_yield=stock_data.get('div_yield'),
                        roe=stock_data.get('roe'),
                        roic=stock_data.get('roic'),
                        margem_liquida=stock_data.get('mrg_liq'),
                        ev_ebit=stock_data.get('ev_ebit'),
                        ev_ebitda=stock_data.get('ev_ebitda'),
                        liquidity=stock_data.get('liquidez_corr'),
                        fonte_dados='fundamentus'
                    )
                    db.add(new_stock)
                    created_count += 1
                    logger.info(f"Criado {ticker}: P/L={new_stock.pl}, ROE={new_stock.roe}, DY={new_stock.div_yield}")
            
            # Commit das alterações
            db.commit()
            
            logger.info(f"Atualização concluída!")
            logger.info(f"Ativos atualizados: {updated_count}")
            logger.info(f"Ativos criados: {created_count}")
            
            # Estatísticas finais
            total_stocks = db.query(Stock).count()
            with_pl = db.query(Stock).filter(Stock.pl.isnot(None)).count()
            with_roe = db.query(Stock).filter(Stock.roe.isnot(None)).count()
            with_dy = db.query(Stock).filter(Stock.div_yield.isnot(None)).count()
            
            logger.info(f"Estatísticas finais:")
            logger.info(f"  Total de ativos: {total_stocks}")
            logger.info(f"  Com P/L: {with_pl}")
            logger.info(f"  Com ROE: {with_roe}")
            logger.info(f"  Com DY: {with_dy}")
        
        # Recalcular scores após atualizar dados
        logger.info("\nRecalculando scores com novos dados...")
        from services.ranking_service import RankingService
        ranking_service = RankingService()
        
        updated_scores = ranking_service.update_ranking()
        logger.info(f"Scores atualizados: {updated_scores} ativos")
        
        return 0
        
    except Exception as e:
        logger.error(f"Erro durante atualização: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())