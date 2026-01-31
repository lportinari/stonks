#!/usr/bin/env python3
"""
Migração para adicionar campos da BrAPI à tabela de stocks
"""

import sys
import os
from sqlalchemy import text

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.database import engine, SessionLocal
from models.stock import Stock

def run_migration():
    """Executa a migração para adicionar novos campos"""
    print("MIGRAÇÃO: Adicionando campos da BrAPI à tabela stocks")
    print("=" * 60)
    
    # Lista de novos campos a serem adicionados
    new_columns = [
        "short_name VARCHAR(200)",
        "currency VARCHAR(10)",
        "logo_url VARCHAR(500)",
        "regular_market_day_high FLOAT",
        "regular_market_day_low FLOAT", 
        "regular_market_day_range VARCHAR(50)",
        "regular_market_change FLOAT",
        "regular_market_change_percent FLOAT",
        "regular_market_time TIMESTAMP WITH TIME ZONE",
        "regular_market_previous_close FLOAT",
        "regular_market_open FLOAT",
        "fifty_two_week_range VARCHAR(50)",
        "fifty_two_week_low FLOAT",
        "fifty_two_week_high FLOAT",
        "price_earnings FLOAT",
        "earnings_per_share FLOAT",
        "volume FLOAT"  # Campo volume que estava faltando
    ]
    
    session = SessionLocal()
    
    try:
        # Verificar quais colunas já existem
        print("Verificando colunas existentes...")
        existing_columns = []
        try:
            result = session.execute(text("PRAGMA table_info(stocks)"))
            columns_info = result.fetchall()
            existing_columns = [col[1] for col in columns_info]
            print(f"Colunas existentes: {len(existing_columns)}")
        except Exception as e:
            print(f"Erro ao verificar colunas existentes: {e}")
            return False
        
        # Adicionar colunas que não existem
        added_columns = 0
        for column_def in new_columns:
            column_name = column_def.split()[0]  # Primeiro palavra é o nome da coluna
            
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE stocks ADD COLUMN {column_def}"
                    session.execute(text(sql))
                    print(f"✅ Adicionada coluna: {column_name}")
                    added_columns += 1
                except Exception as e:
                    print(f"❌ Erro ao adicionar coluna {column_name}: {e}")
            else:
                print(f"⚠️  Coluna {column_name} já existe")
        
        # Commit das alterações
        if added_columns > 0:
            session.commit()
            print(f"\n✅ Migração concluída! {added_columns} colunas adicionadas.")
        else:
            print("\n⚠️  Nenhuma coluna nova precisa ser adicionada.")
        
        # Verificar estrutura final
        print("\nVerificando estrutura final da tabela...")
        try:
            result = session.execute(text("PRAGMA table_info(stocks)"))
            columns_info = result.fetchall()
            print(f"Total de colunas: {len(columns_info)}")
            
            print("\nColunas da tabela stocks:")
            for col in columns_info:
                print(f"  - {col[1]} ({col[2]})")
                
        except Exception as e:
            print(f"Erro ao verificar estrutura final: {e}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erro durante migração: {e}")
        return False
    finally:
        session.close()

def test_new_fields():
    """Testa se os novos campos estão funcionando"""
    print("\nTESTANDO NOVOS CAMPOS")
    print("=" * 40)
    
    session = SessionLocal()
    
    try:
        # Tentar buscar uma ação e acessar novos campos
        stock = session.query(Stock).first()
        
        if stock:
            print(f"Testando com ação: {stock.ticker}")
            
            # Testar campos existentes
            print(f"✅ ticker: {stock.ticker}")
            print(f"✅ empresa: {stock.empresa}")
            print(f"✅ cotacao: {stock.cotacao}")
            
            # Testar novos campos (devem ser None inicialmente)
            print(f"✅ short_name: {stock.short_name}")
            print(f"✅ currency: {stock.currency}")
            print(f"✅ logo_url: {stock.logo_url}")
            print(f"✅ regular_market_day_high: {stock.regular_market_day_high}")
            print(f"✅ regular_market_change_percent: {stock.regular_market_change_percent}")
            print(f"✅ price_earnings: {stock.price_earnings}")
            print(f"✅ volume: {stock.volume}")
            
            print("\n✅ Todos os campos estão acessíveis!")
            return True
        else:
            print("⚠️  Nenhuma ação encontrada no banco para teste")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar campos: {e}")
        return False
    finally:
        session.close()

def main():
    """Função principal"""
    print("MIGRAÇÃO - Adicionando Campos da BrAPI")
    print("=" * 60)
    
    # Executar migração
    if run_migration():
        # Testar novos campos
        if test_new_fields():
            print("\n🎉 Migração concluída com sucesso!")
            print("\nPróximos passos:")
            print("1. Execute: python scripts/schedulers/rotating_updater.py priority")
            print("2. Verifique os dados atualizados na interface web")
            print("3. Teste a página de detalhes das ações")
        else:
            print("\n❌ Migração executada mas testes falharam")
    else:
        print("\n❌ Migração falhou")

if __name__ == "__main__":
    main()