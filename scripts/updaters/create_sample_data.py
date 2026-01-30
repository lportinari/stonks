#!/usr/bin/env python3
"""
Cria dados de exemplo para teste da aplicação
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db, SessionLocal
from models.stock import Stock
from services.ranking_service import RankingService
import logging

def create_sample_data():
    """Cria dados de exemplo de ações brasileiras"""
    
    print("Criando dados de exemplo...")
    
    # Inicializa banco
    init_db()
    
    # Dados de exemplo de ações brasileiras
    sample_stocks = [
        {
            'ticker': 'VALE3',
            'empresa': 'Vale S.A.',
            'setor': 'Mineração',
            'cotacao': 68.50,
            'div_yield': 11.5,
            'pl': 6.8,
            'pvp': 1.2,
            'roe': 18.5,
            'margem_liquida': 25.8,
            'ev_ebitda': 4.5
        },
        {
            'ticker': 'PETR4',
            'empresa': 'Petróleo Brasileiro S.A.',
            'setor': 'Petróleo e Gás',
            'cotacao': 35.20,
            'div_yield': 13.2,
            'pl': 5.5,
            'pvp': 0.9,
            'roe': 15.8,
            'margem_liquida': 12.5,
            'ev_ebitda': 3.8
        },
        {
            'ticker': 'ITUB4',
            'empresa': 'Itaú Unibanco S.A.',
            'setor': 'Financeiro',
            'cotacao': 32.80,
            'div_yield': 6.8,
            'pl': 10.2,
            'pvp': 1.8,
            'roe': 20.5,
            'margem_liquida': 28.5,
            'ev_ebitda': 8.5
        },
        {
            'ticker': 'BBDC4',
            'empresa': 'Banco Bradesco S.A.',
            'setor': 'Financeiro',
            'cotacao': 22.50,
            'div_yield': 7.2,
            'pl': 9.8,
            'pvp': 1.6,
            'roe': 19.2,
            'margem_liquida': 26.8,
            'ev_ebitda': 7.9
        },
        {
            'ticker': 'WEGE3',
            'empresa': 'WEG S.A.',
            'setor': 'Bens Industriais',
            'cotacao': 45.60,
            'div_yield': 2.8,
            'pl': 28.5,
            'pvp': 4.2,
            'roe': 22.5,
            'margem_liquida': 18.5,
            'ev_ebitda': 12.5
        },
        {
            'ticker': 'GGBR4',
            'empresa': 'Gerdau S.A.',
            'setor': 'Siderurgia',
            'cotacao': 28.90,
            'div_yield': 8.5,
            'pl': 8.2,
            'pvp': 0.8,
            'roe': 12.8,
            'margem_liquida': 8.5,
            'ev_ebitda': 5.8
        },
        {
            'ticker': 'MGLU3',
            'empresa': 'Magazine Luiza S.A.',
            'setor': 'Varejo',
            'cotacao': 3.85,
            'div_yield': 0.0,
            'pl': -15.2,
            'pvp': 0.5,
            'roe': -8.5,
            'margem_liquida': -2.8,
            'ev_ebitda': 18.5
        },
        {
            'ticker': 'B3SA3',
            'empresa': 'B3 S.A.',
            'setor': 'Financeiro',
            'cotacao': 15.20,
            'div_yield': 4.5,
            'pl': 12.8,
            'pvp': 2.8,
            'roe': 16.5,
            'margem_liquida': 35.8,
            'ev_ebitda': 9.8
        },
        {
            'ticker': 'ABEV3',
            'empresa': 'Ambev S.A.',
            'setor': 'Bens de Consumo',
            'cotacao': 14.50,
            'div_yield': 4.8,
            'pl': 18.5,
            'pvp': 3.2,
            'roe': 25.5,
            'margem_liquida': 28.5,
            'ev_ebitda': 11.2
        },
        {
            'ticker': 'BBAS3',
            'empresa': 'Banco do Brasil S.A.',
            'setor': 'Financeiro',
            'cotacao': 48.50,
            'div_yield': 9.2,
            'pl': 6.8,
            'pvp': 1.1,
            'roe': 14.8,
            'margem_liquida': 22.5,
            'ev_ebitda': 6.2
        }
    ]
    
    # Limpa dados existentes
    session = SessionLocal()
    try:
        session.query(Stock).delete()
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
    
    # Insere dados de exemplo
    session = SessionLocal()
    try:
        for stock_data in sample_stocks:
            stock = Stock(**stock_data)
            session.add(stock)
        
        session.commit()
        print(f"Inseridos {len(sample_stocks)} registros de exemplo")
    except:
        session.rollback()
        raise
    finally:
        session.close()
    
    # Testa ranking
    ranking_service = RankingService()
    ranking_service.update_ranking()
    ranked_stocks = ranking_service.get_top_stocks(limit=10)
    
    print("\nTop 5 ações por ranking:")
    for i, stock in enumerate(ranked_stocks[:5], 1):
        print(f"{i}. {stock.ticker} - Score: {stock.score_final:.2f} - Setor: {stock.setor}")
    
    print("\nDados de exemplo criados com sucesso!")

if __name__ == "__main__":
    create_sample_data()