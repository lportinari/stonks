#!/usr/bin/env python3
"""
Script de migração para adicionar coluna de classe de ativo na tabela purchases
"""

import sqlite3
import os
import sys

def add_classe_ativo_column():
    """Adiciona a coluna classe_ativo à tabela purchases"""
    
    # Caminho do banco de dados
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'stocks.db')
    
    if not os.path.exists(db_path):
        print(f"✗ Banco de dados não encontrado em: {db_path}")
        return False
    
    print(f"Conectando ao banco de dados: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(purchases)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'classe_ativo' in columns:
            print("✓ Coluna 'classe_ativo' já existe na tabela purchases")
            return True
        
        # Adicionar a coluna
        print("Adicionando coluna 'classe_ativo' à tabela purchases...")
        cursor.execute('''
            ALTER TABLE purchases 
            ADD COLUMN classe_ativo VARCHAR(50) DEFAULT NULL
        ''')
        
        conn.commit()
        print("✓ Coluna 'classe_ativo' adicionada com sucesso!")
        
        # Criar índice para melhor performance
        print("Criando índice para coluna 'classe_ativo'...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_purchases_classe_ativo 
            ON purchases(classe_ativo)
        ''')
        
        conn.commit()
        print("✓ Índice criado com sucesso!")
        
        print("\n✅ Migração concluída com sucesso!")
        print("\nClasses de ativos disponíveis:")
        print("- Ações")
        print("- Renda Fixa Pós")
        print("- Renda Fixa Dinâmica")
        print("- Fundos Imobiliários")
        print("- Internacional")
        print("- Fundos Multimercados")
        print("- Alternativos")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao adicionar coluna: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRAÇÃO: Adicionar coluna de classe de ativo")
    print("=" * 60)
    print()
    
    if add_classe_ativo_column():
        sys.exit(0)
    else:
        sys.exit(1)