#!/usr/bin/env python3
"""
Teste simples para obter dados reais do Yahoo Finance
"""

import yfinance as yf
import time

def test_yahoo_simple():
    print("TESTE SIMPLES YAHOO FINANCE")
    print("="*40)
    
    try:
        # Testar PETR4 diretamente
        print("Buscando PETR4...")
        ticker = yf.Ticker("PETR4.SA")
        
        # Obter informações básicas
        info = ticker.info
        
        print("DADOS OBTIDOS:")
        print(f"Preço: {info.get('regularMarketPrice', 'N/A')}")
        print(f"Empresa: {info.get('longName', 'N/A')}")
        print(f"Setor: {info.get('sector', 'N/A')}")
        print(f"DY: {info.get('dividendYield', 'N/A')}")
        print(f"P/L: {info.get('forwardPE', 'N/A')}")
        
        if info.get('regularMarketPrice'):
            print("\nSUCESSO: Dados reais obtidos!")
            return True
        else:
            print("\nFALHA: Sem preço de mercado")
            return False
            
    except Exception as e:
        print(f"\nERRO: {e}")
        return False

def test_multiple_tickers():
    print("\nTESTE MULTIPLOS TICKERS")
    print("="*40)
    
    tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA']
    
    for ticker_symbol in tickers:
        try:
            print(f"\n{ticker_symbol}:")
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            price = info.get('regularMarketPrice')
            
            if price:
                print(f"  Preço: R$ {price:.2f} ✅")
            else:
                print(f"  Preço: N/A ❌")
                
        except Exception as e:
            print(f"  Erro: {e} ❌")
        
        # Delay para evitar rate limiting
        time.sleep(2)

if __name__ == "__main__":
    success = test_yahoo_simple()
    
    if success:
        test_multiple_tickers()
    else:
        print("\nYahoo Finance não está funcionando corretamente")
        print("Possíveis causas:")
        print("1. Rate limiting (muitas requisições)")
        print("2. Problema de conexão")
        print("3. API do Yahoo Finance instável")