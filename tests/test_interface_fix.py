#!/usr/bin/env python3
"""
Script para diagnosticar e resolver o problema da interface web
mostrando apenas 10 ações quando o banco tem mais.
"""

import sys
import os
from models.database import SessionLocal
from models.stock import Stock
from services.ranking_service import RankingService
from services.cache_manager import CacheManager

def diagnose_and_fix():
    print("DIAGNOSTICO COMPLETO DO PROBLEMA DA INTERFACE")
    print("=" * 60)
    
    # 1. Verificar banco de dados
    print("\n1. VERIFICANDO BANCO DE DADOS:")
    session = SessionLocal()
    
    total_stocks = session.query(Stock).count()
    stocks_with_price = session.query(Stock).filter(
        Stock.cotacao.isnot(None)
    ).filter(Stock.cotacao > 0).count()
    
    stocks_with_score = session.query(Stock).filter(
        Stock.score_final.isnot(None)
    ).count()
    
    print(f"   Total de ações: {total_stocks}")
    print(f"   Ações com preço: {stocks_with_price}")
    print(f"   Ações com score: {stocks_with_score}")
    
    # 2. Testar RankingService
    print("\n2. TESTANDO RANKINGSERVICE:")
    ranking = RankingService()
    
    for limit in [10, 20, 30]:
        stocks = ranking.get_current_ranking(limit=limit)
        print(f"   Limit={limit}: {len(stocks)} ações retornadas")
        
        if len(stocks) > 0:
            print(f"     Primeira: {stocks[0].ticker}")
            print(f"     Última: {stocks[-1].ticker}")
    
    # 3. Limpar cache
    print("\n3. LIMPANDO CACHE:")
    cache_manager = CacheManager()
    cache_manager.clear_all()
    print("   Cache limpo com sucesso!")
    
    # 4. Análise do problema
    print("\n4. ANÁLISE DO PROBLEMA:")
    
    if stocks_with_price > 10:
        test_30 = ranking.get_current_ranking(limit=30)
        if len(test_30) > 10:
            print("   ✅ RankingService funciona corretamente!")
            print("   ✅ Problema está no cache ou no servidor web!")
            print("\n   SOLUÇÃO:")
            print("   1. Reinicie o servidor web: python app.py")
            print("   2. Acesse: http://localhost:5000")
            print("   3. A interface deve mostrar todas as ações!")
        else:
            print("   ❌ RankingService ainda limitado a 10 ações")
            print("   ❌ Precisa verificar a modificação no código")
    else:
        print("   ❌ Banco tem menos de 10 ações com preço")
        print("   ❌ Precisa adicionar mais ações com dados")
        print("\n   SOLUÇÃO:")
        print("   Execute: python fix_rotating_system.py all")
    
    session.close()
    
    # 5. Exibir ações atuais
    print("\n5. TOP 15 AÇÕES ATUAIS:")
    stocks_top = ranking.get_current_ranking(limit=15)
    
    for i, stock in enumerate(stocks_top, 1):
        price = stock.cotacao if stock.cotacao else 0
        score = stock.score_final if stock.score_final else 0
        source = stock.fonte_dados or "unknown"
        
        if score:
            score_text = f"{score:6.1f}"
        else:
            score_text = "  N/A  "
        
        print(f"   {i:2d}. {stock.ticker:8s} | R$ {price:7.2f} | Score: {score_text} | {source[:12]}")

if __name__ == "__main__":
    diagnose_and_fix()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMO FINAL:")
    print("Se o RankingService retorna > 10 ações:")
    print("   ✅ Problema resolvido!")
    print("   ✅ Reinicie o servidor e acesse a interface")
    print("\nSe ainda retorna apenas 10 ações:")
    print("   ❌ Verificar modifications em services/ranking_service.py")
    print("   ❌ Reiniciar servidor completamente")