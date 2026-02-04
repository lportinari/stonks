#!/usr/bin/env python3
"""
Script para limpar todos os dados da tabela de ações
"""

import sys
import os

# Adicionar diretório raiz ao path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from models.database import SessionLocal
from models.stock import Stock

def clear_stocks():
    """Remove todos os registros da tabela de ações"""
    
    print("=" * 60)
    print("LIMPANDO DADOS DE AÇÕES")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # Contar registros antes de deletar
        count = session.query(Stock).count()
        print(f"\nRegistros encontrados: {count}")
        
        if count > 0:
            # Confirmar antes de deletar
            response = input(f"\nTem certeza que deseja deletar {count} registros? (s/N): ")
            if response.lower() != 's':
                print("❌ Operação cancelada")
                return
            
            # Deletar todos os registros
            session.query(Stock).delete()
            session.commit()
            print(f"✅ {count} registros deletados com sucesso!")
        else:
            print("✅ A tabela já está vazia")
            
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao limpar dados: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    # Verificar resultado
    session = SessionLocal()
    try:
        final_count = session.query(Stock).count()
        print(f"\nRegistros restantes: {final_count}")
        
        if final_count == 0:
            print("✅ Tabela de ações limpa com sucesso!")
        else:
            print(f"⚠️  Ainda há {final_count} registros na tabela")
            
    except Exception as e:
        print(f"❌ Erro ao verificar resultado: {e}")
    finally:
        session.close()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    clear_stocks()