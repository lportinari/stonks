#!/usr/bin/env python3
"""
Atualização rápida com dados reais para verificação imediata
"""

import time
from get_real_quotes import get_real_quote
from models.database import SessionLocal
from models.stock import Stock
from services.ranking_service import RankingService
from services.cache_manager import CacheManager

def quick_update_real():
    """Atualização rápida das principais ações"""
    
    print("ATUALIZAÇÃO RÁPIDA COM DADOS REAIS")
    print("=" * 50)
    
    # Apenas as top 5 para teste rápido
    top_tickers = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3']
    
    session = SessionLocal()
    updated = 0
    
    for ticker in top_tickers:
        print(f"\nAtualizando {ticker}...")
        
        # Obter dado real (com delays curtos)
        data = get_real_quote(ticker)
        
        if data and data.get('success') and data.get('cotacao'):
            # Atualizar no banco
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if stock:
                old_price = stock.cotacao
                stock.cotacao = data['cotacao']
                stock.fonte_dados = data['fonte_dados']
                stock.data_atualizacao = data['data_atualizacao']
                updated += 1
                
                print(f"  SUCESSO: R$ {old_price:.2f} → R$ {data['cotacao']:.2f}")
                print(f"  FONTE: {data['fonte_dados']}")
        else:
            print(f"  FALHA: Sem dados para {ticker}")
    
    # Commit
    session.commit()
    
    # Recalcular scores
    print(f"\nRecalculando scores...")
    ranking_service = RankingService()
    cache_manager = CacheManager()
    
    score_count = ranking_service.update_ranking()
    cache_manager.clear_all()
    
    session.close()
    
    print(f"\nRESULTADO:")
    print(f"- Ações atualizadas: {updated}")
    print(f"- Scores recalculados: {score_count}")
    print(f"- Cache limpo: Sim")
    print(f"- Interface pronta: Sim")
    
    if updated > 0:
        print(f"\n✅ INTERFACE ATUALIZADA COM DADOS REAIS!")
        print(f"🌐 Acesse agora: http://localhost:5000")
    else:
        print(f"\n❌ Nenhuma ação atualizada")
    
    return updated

if __name__ == "__main__":
    start_time = time.time()
    updated = quick_update_real()
    elapsed = time.time() - start_time
    
    print(f"\n⏱️ Tempo total: {elapsed:.1f} segundos")
    print(f"📊 Taxa de sucesso: {(updated/5)*100:.0f}%")