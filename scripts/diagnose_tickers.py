#!/usr/bin/env python3
"""
Diagnóstico de Tickers - Testa múltiplos tickers para identificar problemas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.professional_apis import ProfessionalAPIService

def test_tickers(tickers):
    """Testa múltiplos tickers e retorna resultados"""
    api = ProfessionalAPIService()
    results = {}
    
    print(f"TESTANDO {len(tickers)} TICKERS")
    print("=" * 60)
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i:2d}/{len(tickers)}] {ticker}...", end=" ")
        
        data = api.get_from_brapi(ticker)
        
        if data and data.get('success'):
            price = data.get('cotacao', 0)
            indicators = sum(1 for k, v in data.items() if v is not None and k not in ['success', 'ticker', 'fonte_dados', 'data_atualizacao'])
            print(f"✅ R$ {price:.2f} ({indicators} indicadores)")
            results[ticker] = {'success': True, 'price': price, 'indicators': indicators}
        else:
            print(f"❌ FALHA")
            results[ticker] = {'success': False}
    
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    
    successful = sum(1 for r in results.values() if r['success'])
    print(f"Sucesso: {successful}/{len(tickers)} ({successful/len(tickers)*100:.1f}%)")
    print(f"Falha: {len(tickers) - successful}/{len(tickers)}")
    
    if successful > 0:
        avg_indicators = sum(r['indicators'] for r in results.values() if r['success']) / successful
        print(f"Média de indicadores: {avg_indicators:.1f}")
    
    return results

if __name__ == "__main__":
    # Testar tickers comuns com diferentes padrões
    test_groups = {
        "Padrão 4 (Comum)": ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3', 'MGLU3', 'B3SA3', 'ABEV3'],
        "Padrão 11 (Bancos)": ['BPAC11', 'ITSA4', 'SANB11', 'SULA11'],
        "Padrão 3 (Antigo)": ['PETR3', 'VALE5', 'ITUB3', 'BBDC3', 'WEGE4', 'MGLU4', 'B3SA4'],
        "Padrão 12 (Bancos)": ['BAU4', 'BBSE3', 'BPAN4', 'CASH3', 'CXSE3'],
        "FIIs": ['HGLG11', 'XPML11', 'KNRI11', 'HGRE11'],
    }
    
    all_results = {}
    
    for group_name, tickers in test_groups.items():
        print(f"\n\n{'='*60}")
        print(f"GRUPO: {group_name}")
        print(f"{'='*60}")
        results = test_tickers(tickers)
        all_results[group_name] = results
    
    print(f"\n\n{'='*60}")
    print("ANÁLISE FINAL")
    print(f"{'='*60}")
    
    for group_name, results in all_results.items():
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        status = "✅" if successful == total else "⚠️" if successful > 0 else "❌"
        print(f"{status} {group_name}: {successful}/{total}")
    
    # Identificar tickers problemáticos
    print(f"\n\nTICKERS COM FALHA:")
    problem_tickers = []
    for group_name, results in all_results.items():
        for ticker, result in results.items():
            if not result['success']:
                problem_tickers.append((group_name, ticker))
    
    if problem_tickers:
        for group, ticker in problem_tickers:
            print(f"  ❌ {ticker} ({group})")
    else:
        print("  ✅ Todos os tickers funcionaram!")