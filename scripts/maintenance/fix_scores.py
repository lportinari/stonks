#!/usr/bin/env python3
"""
Script para corrigir scores das ações que não têm cálculo
"""

from models.database import SessionLocal
from models.stock import Stock
from services.indicator_calculator import IndicatorCalculator
from config import Config

def main():
    print("=== CORRIGINDO SCORES DAS AÇÕES ===\n")
    
    session = SessionLocal()
    calculator = IndicatorCalculator()
    weights = Config.DEFAULT_WEIGHTS.copy()
    
    try:
        # Buscar todas as ações sem score
        stocks_no_score = session.query(Stock).filter(Stock.score_final.is_(None)).all()
        
        print(f"Ações sem score: {len(stocks_no_score)}")
        
        for stock in stocks_no_score:
            print(f"\nProcessando {stock.ticker}...")
            
            # Verificar dados
            print(f"  DY: {stock.div_yield}")
            print(f"  P/L: {stock.pl}")
            print(f"  P/VP: {stock.pvp}")
            print(f"  ROE: {stock.roe}")
            print(f"  Margem: {stock.margem_liquida}")
            
            # Tentar calcular score
            stock_dict = stock.to_dict()
            score = calculator.calculate_stock_score(stock_dict, weights)
            
            if score is not None:
                stock.score_final = score
                print(f"  Score calculado: {score:.2f}")
            else:
                print(f"  Não foi possível calcular score")
        
        # Commit das alterações
        session.commit()
        print(f"\n{session.query(Stock).filter(Stock.score_final.isnot(None)).count()} ações agora têm score!")
        
        # Atualizar posições do ranking
        stocks_with_score = session.query(Stock).filter(Stock.score_final.isnot(None)).order_by(Stock.score_final.desc()).all()
        for i, stock in enumerate(stocks_with_score, 1):
            stock.rank_posicao = i
        
        session.commit()
        print("Posições do ranking atualizadas!")
        
    except Exception as e:
        session.rollback()
        print(f"Erro: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()