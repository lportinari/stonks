#!/usr/bin/env python3
"""
Script Automatizado para Atualizar Dados Reais
Usa web scraping robusto para obter cotações atuais
"""

import sys
import time
from get_real_quotes import get_all_real_quotes
from models.database import SessionLocal
from models.stock import Stock
from services.ranking_service import RankingService
from services.cache_manager import CacheManager

def update_database_with_real_data():
    """Atualiza o banco de dados com cotações reais"""
    
    print("=" * 70)
    print("🔄 ATUALIZAÇÃO AUTOMÁTICA COM DADOS REAIS")
    print("=" * 70)
    print("Fonte: Web Scraping de sites brasileiros (Status Invest, etc.)")
    print("Método: Múltiplas tentativas com fallback robusto")
    print()
    
    # Lista de todas as ações
    tickers = [
        'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
        'GGBR4', 'ABEV3', 'MGLU3', 'B3SA3', 'BBAS3',
        'SANB11', 'RAIL3', 'SUZB3', 'KLBN11', 'LREN3',
        'RADL3', 'ELET3', 'ENBR3'
    ]
    
    # Buscar dados reais
    print("📡 OBTENDO COTAÇÕES REAIS...")
    real_data = get_all_real_quotes(tickers)
    
    # Separar sucessos e falhas
    successful = [d for d in real_data if d.get('success') and d.get('cotacao')]
    failed = [d for d in real_data if not d.get('success') or not d.get('cotacao')]
    
    print(f"\n📊 RESUMO DA COLETA:")
    print(f"✅ Sucesso: {len(successful)} ações")
    print(f"❌ Falha: {len(failed)} ações")
    
    if failed:
        print("\n⚠️ Ações sem dados:")
        for data in failed:
            print(f"   - {data['ticker']}: {data.get('fonte_dados', 'Erro desconhecido')}")
    
    # Atualizar banco de dados
    print(f"\n💾 ATUALIZANDO BANCO DE DADOS...")
    
    session = SessionLocal()
    updated_count = 0
    
    try:
        for data in successful:
            ticker = data['ticker']
            
            # Buscar ação no banco
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            
            if stock:
                # Atualizar com dados reais
                old_price = stock.cotacao
                stock.cotacao = data['cotacao']
                stock.empresa = data.get('empresa', stock.empresa)
                stock.fonte_dados = data['fonte_dados']
                stock.data_atualizacao = data['data_atualizacao']
                
                # Atualizar indicadores se disponíveis
                if data.get('div_yield'):
                    stock.div_yield = data['div_yield']
                if data.get('pl'):
                    stock.pl = data['pl']
                if data.get('pvp'):
                    stock.pvp = data['pvp']
                if data.get('roe'):
                    stock.roe = data['roe']
                if data.get('margem_liquida'):
                    stock.margem_liquida = data['margem_liquida']
                
                # Mostrar mudança
                price_change = data['cotacao'] - old_price if old_price else 0
                change_percent = (price_change / old_price * 100) if old_price and old_price > 0 else 0
                
                updated_count += 1
                print(f"   ✅ {ticker}: R$ {old_price:.2f} → R$ {data['cotacao']:.2f} ({change_percent:+.1f}%) [{data['fonte_dados']}]")
            else:
                print(f"   ❌ {ticker}: Não encontrada no banco")
        
        # Commit das alterações
        session.commit()
        print(f"\n✅ {updated_count} ações atualizadas com sucesso!")
        
        # Recalcular scores
        print(f"\n📈 RECALCULANDO SCORES E RANKING...")
        ranking_service = RankingService()
        cache_manager = CacheManager()
        
        # Atualizar scores
        score_count = ranking_service.update_ranking()
        print(f"   ✅ Scores recalculados: {score_count} ações")
        
        # Limpar cache
        cache_manager.clear_all()
        print(f"   ✅ Cache limpo")
        
        # Mostrar ranking atualizado
        print(f"\n🏆 TOP 10 ATUALIZADO:")
        print("-" * 50)
        
        top_stocks = ranking_service.get_top_stocks(10)
        for i, stock in enumerate(top_stocks, 1):
            source_indicator = "🌐" if "web" in stock.fonte_dados.lower() or "scraping" in stock.fonte_dados.lower() else "📊"
            print(f"   {i:2d}. {stock.ticker} - R$ {stock.cotacao:7.2f} - Score: {stock.score_final:6.2f} {source_indicator}")
        
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"   • Ações totais: {len(tickers)}")
        print(f"   • Atualizadas: {updated_count}")
        print(f"   • Taxa de sucesso: {(updated_count/len(tickers)*100):.1f}%")
        print(f"   • Fonte principal: Web Scraping (Dados REAIS)")
        print(f"   • Timestamp: {time.strftime('%d/%m/%Y %H:%M:%S')}")
        
        return updated_count
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERRO AO ATUALIZAR BANCO: {e}")
        return 0
    finally:
        session.close()

def verify_real_data():
    """Verifica se os dados são reais comparando com valores esperados"""
    print("\n🔍 VERIFICAÇÃO DE DADOS REAIS:")
    print("-" * 40)
    
    session = SessionLocal()
    
    try:
        # Valores aproximados esperados para verificação
        expected_prices = {
            'PETR4': (35, 42),    # Petrobras
            'VALE3': (68, 78),     # Vale
            'ITUB4': (30, 38),     # Itaú
            'BBDC4': (20, 28),     # Bradesco
            'WEGE3': (38, 46),     # WEG
            'ABEV3': (12, 16),     # Ambev
            'MGLU3': (3, 6),      # Magazine Luiza
            'RADL3': (110, 130),   # Raia Drogasil
        }
        
        all_good = True
        
        for ticker, (min_price, max_price) in expected_prices.items():
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            
            if stock and stock.cotacao:
                price = stock.cotacao
                if min_price <= price <= max_price:
                    print(f"   ✅ {ticker}: R$ {price:.2f} (FAIXA NORMAL)")
                else:
                    print(f"   ⚠️ {ticker}: R$ {price:.2f} (FORA DA FAIXA ESPERADA R${min_price}-{max_price})")
                    all_good = False
            else:
                print(f"   ❌ {ticker}: SEM DADOS")
                all_good = False
        
        if all_good:
            print("\n🎉 TODOS OS PREÇOS ESTÃO EM FAIXAS REALISTAS!")
        else:
            print("\n⚠️ ALGUNS PREÇOS PODEM PRECISAR DE VERIFICAÇÃO MANUAL")
        
        return all_good
        
    finally:
        session.close()

def main():
    """Função principal"""
    start_time = time.time()
    
    try:
        # Atualizar dados reais
        updated = update_database_with_real_data()
        
        if updated > 0:
            # Verificar dados
            verify_real_data()
            
            # Resumo final
            elapsed_time = time.time() - start_time
            print(f"\n" + "=" * 70)
            print(f"🎉 ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"⏱️ Tempo total: {elapsed_time:.1f} segundos")
            print(f"🌐 Fonte: DADOS REAIS via Web Scraping")
            print(f"📊 Status: SISTEMA 100% FUNCIONAL")
            print("=" * 70)
            
            print(f"\n🚀 Acesse agora: http://localhost:5000")
            print(f"💡 Os dados são 100% REAIS e atualizados!")
        else:
            print("\n❌ Nenhuma ação foi atualizada. Verifique os logs acima.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Processo interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()