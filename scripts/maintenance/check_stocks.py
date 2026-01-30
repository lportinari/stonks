#!/usr/bin/env python3
"""
Script simples para verificar quantas ações estão configuradas
"""

from services.hybrid_scraper import HybridScraper
from models.database import SessionLocal
from models.stock import Stock

def main():
    print("=== VERIFICAÇÃO DE AÇÕES ===\n")
    
    # Verificar configuração no scraper
    scraper = HybridScraper()
    configured_stocks = list(scraper.manual_data.keys())
    
    print(f"Ações configuradas no scraper: {len(configured_stocks)}")
    print("Tickers configurados:")
    for ticker in sorted(configured_stocks):
        print(f"  {ticker}")
    
    print("\n" + "="*50)
    
    # Verificar ações no banco de dados
    session = SessionLocal()
    try:
        db_stocks = session.query(Stock).all()
        print(f"\nAções no banco de dados: {len(db_stocks)}")
        
        db_tickers = [stock.ticker for stock in db_stocks]
        print("Tickers no banco:")
        for ticker in sorted(db_tickers):
            print(f"  {ticker}")
        
        print("\n" + "="*50)
        
        # Comparar
        configured_set = set(configured_stocks)
        db_set = set(db_tickers)
        
        missing_in_db = configured_set - db_set
        extra_in_db = db_set - configured_set
        
        if missing_in_db:
            print(f"\nAções configuradas mas não no banco ({len(missing_in_db)}):")
            for ticker in sorted(missing_in_db):
                print(f"  {ticker}")
        
        if extra_in_db:
            print(f"\nAções no banco mas não configuradas ({len(extra_in_db)}):")
            for ticker in sorted(extra_in_db):
                print(f"  {ticker}")
        
        if not missing_in_db and not extra_in_db:
            print("\n✅ Banco de dados está sincronizado com a configuração!")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()