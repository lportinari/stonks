#!/usr/bin/env python3
"""
Script para recalcular scores de todas as ações com o mapeamento corrigido
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from models.database import SessionLocal
from models.stock import Stock
from services.indicator_calculator import IndicatorCalculator
from services.ranking_service import RankingService
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=== RECALCULANDO SCORES DE TODAS AS AÇÕES ===\n")
    
    session = SessionLocal()
    calculator = IndicatorCalculator()
    ranking_service = RankingService()
    weights = Config.DEFAULT_WEIGHTS.copy()
    
    try:
        # Buscar todas as ações
        all_stocks = session.query(Stock).all()
        print(f"Total de ações no banco: {len(all_stocks)}")
        
        # Contadores
        updated_count = 0
        error_count = 0
        
        for stock in all_stocks:
            print(f"\nProcessando {stock.ticker}...")
            
            # Converter para dicionário
            stock_dict = stock.to_dict()
            
            # Verificar dados disponíveis
            indicators = {
                'DY': stock.div_yield,
                'P/L': stock.pl,
                'P/VP': stock.pvp,
                'ROE': stock.roe,
                'Margem Líquida': stock.margem_liquida
            }
            
            print(f"  Indicadores disponiveis:")
            for name, value in indicators.items():
                status = "OK" if value is not None else "X"
                print(f"    {name}: {status} {value if value is not None else 'None'}")
            
            # Tentar calcular score
            score = calculator.calculate_stock_score(stock_dict, weights)
            
            if score is not None:
                old_score = stock.score_final
                stock.score_final = score
                print(f"  Score calculado: {score:.2f} {'(antigo: ' + str(old_score) if old_score else 'novo)'}")
                updated_count += 1
            else:
                print(f"  [ERRO] Nao foi possivel calcular score")
                error_count += 1
        
        # Commit das alterações
        session.commit()
        print(f"\n[OK] {updated_count} acoes tiveram scores atualizados!")
        print(f"[ERRO] {error_count} acoes nao puderam ter score calculado")
        
        # Atualizar posições do ranking
        print("\n=== ATUALIZANDO POSICOES DO RANKING ===")
        stocks_with_score = session.query(Stock).filter(
            Stock.score_final.isnot(None)
        ).order_by(Stock.score_final.desc()).all()
        
        print(f"Acoes com score: {len(stocks_with_score)}")
        
        for i, stock in enumerate(stocks_with_score, 1):
            stock.rank_posicao = i
        
        session.commit()
        print("[OK] Posicoes do ranking atualizadas!")
        
        # Estatísticas finais
        print("\n=== ESTATISTICAS FINAIS ===")
        total_stocks = session.query(Stock).count()
        stocks_with_score = session.query(Stock).filter(
            Stock.score_final.isnot(None)
        ).count()
        
        print(f"Total de acoes: {total_stocks}")
        print(f"Acoes com score: {stocks_with_score}")
        print(f"Acoes sem score: {total_stocks - stocks_with_score}")
        print(f"Taxa de cobertura: {(stocks_with_score/total_stocks*100):.1f}%")
        
        # Top 10
        top_stocks = stocks_with_score[:10]
        print(f"\n[TOP 10] ACOES:")
        for i, stock in enumerate(top_stocks, 1):
            print(f"  {i:2d}. {stock.ticker} - Score: {stock.score_final:.1f} - {stock.empresa[:30]}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Erro durante processamento: {e}")
        print(f"[ERRO] Erro: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()