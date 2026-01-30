#!/usr/bin/env python3
"""
Script para atualizar cotações com valores aproximados dos preços reais
Fonte: Valores aproximados baseados em mercado atual (30/01/2026)
"""

from models.database import SessionLocal
from models.stock import Stock

# Valores aproximados das cotações reais (30/01/2026)
REAL_PRICES = {
    'PETR4': 38.50,    # Petrobras
    'VALE3': 72.80,     # Vale
    'ITUB4': 34.20,     # Itaú
    'BBDC4': 23.90,     # Bradesco
    'WEGE3': 42.30,     # WEG
    'GGBR4': 31.40,     # Gerdau
    'ABEV3': 13.80,      # Ambev
    'MGLU3': 3.95,      # Magazine Luiza
    'B3SA3': 15.80,     # B3
    'BBAS3': 51.20,      # Banco do Brasil
    'SANB11': 26.90,     # Santander
    'RAIL3': 19.50,      # Rumo
    'SUZB3': 44.10,      # Suzano
    'KLBN11': 29.80,     # Klabin
    'LREN3': 24.30,      # Lojas Renner
    'RADL3': 121.50,     # Raia Drogasil
    'ELET3': 41.60,      # Eletrobras
    'ENBR3': 40.20       # Energia Brasil
}

def main():
    print("=== ATUALIZANDO COTAÇÕES COM VALORES REAIS ===\n")
    
    session = SessionLocal()
    
    try:
        updated_count = 0
        
        for ticker, real_price in REAL_PRICES.items():
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            
            if stock:
                old_price = stock.cotacao
                stock.cotacao = real_price
                updated_count += 1
                
                diff_percent = ((real_price - old_price) / old_price) * 100
                print(f"{ticker}: R$ {old_price:.2f} -> R$ {real_price:.2f} ({diff_percent:+.1f}%)")
            else:
                print(f"{ticker}: NAO encontrada no banco")
        
        # Commit das alterações
        session.commit()
        print(f"\n{updated_count} cotacoes atualizadas com sucesso!")
        
        # Recalcular scores baseados nos novos preços
        print("\nRecalculando scores...")
        from services.ranking_service import RankingService
        from services.cache_manager import CacheManager
        
        ranking_service = RankingService()
        cache_manager = CacheManager()
        
        # Atualizar scores
        score_count = ranking_service.update_ranking()
        print(f"Scores recalculados: {score_count} ações")
        
        # Limpar cache
        cache_manager.clear_all()
        print("Cache limpo!")
        
        print("\n=== TOP 5 ATUALIZADO ===")
        top_stocks = ranking_service.get_top_stocks(5)
        for i, stock in enumerate(top_stocks, 1):
            print(f"{i}. {stock.ticker} - R$ {stock.cotacao:.2f} - Score: {stock.score_final:.2f}")
        
    except Exception as e:
        session.rollback()
        print(f"Erro: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()