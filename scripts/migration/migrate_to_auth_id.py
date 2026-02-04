"""
Script de migração para converter user_id para auth_id na tabela purchases

Este script:
1. Adiciona a coluna auth_id temporariamente
2. Zera a tabela purchases (opcional - descomente se necessário)
3. Remove a coluna user_id
4. Renomeia auth_id para auth_id

Execute com: python -m scripts.migration.migrate_to_auth_id
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from config import Config
from sqlalchemy import text, create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker

def migrate_database():
    """Executa a migração do banco de dados"""
    
    engine = create_engine(Config.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("Iniciando migração do banco de dados...")
        print(f"Banco de dados: {Config.DATABASE_URL}")
        
        # Verificar se a tabela purchases existe
        inspector = inspect(engine)
        if 'purchases' not in inspector.get_table_names():
            print("ERRO: Tabela 'purchases' não encontrada!")
            print("Execute primeiro os scripts de inicialização do banco de dados.")
            return False
        
        # Verificar colunas atuais
        columns = [col['name'] for col in inspector.get_columns('purchases')]
        print(f"\nColunas atuais: {columns}")
        
        # Verificar se já tem auth_id
        if 'auth_id' in columns:
            print("\nAVISO: Coluna auth_id já existe!")
            if 'user_id' in columns:
                print("Removendo coluna user_id...")
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE purchases DROP COLUMN user_id"))
                    conn.commit()
                    print("✓ Coluna user_id removida")
            else:
                print("Migração já concluída anteriormente.")
            return True
        
        # Se tem user_id, vamos migrar
        if 'user_id' in columns:
            print("\nIniciando migração de user_id para auth_id...")
            
            with engine.connect() as conn:
                # Passo 1: Adicionar coluna auth_id (temporariamente nullable)
                conn.execute(text("ALTER TABLE purchases ADD COLUMN auth_id VARCHAR(36)"))
                conn.commit()
                print("✓ Coluna auth_id adicionada")
                
                # Passo 2: ZERAR a tabela (OPCIONAL - descomente se necessário)
                print("\nAVISO: Dados existentes serão perdidos!")
                print("Se você quiser preservar dados, edite este script.")
                
                # Descomente as linhas abaixo para ZERAR a tabela:
                # confirm = input("Deseja zerar a tabela purchases? (s/n): ")
                # if confirm.lower() == 's':
                #     conn.execute(text("DELETE FROM purchases"))
                #     conn.commit()
                #     print("✓ Tabela zerada")
                
                # Por padrão, vamos zerar pois user_id não pode ser convertido para UUID
                conn.execute(text("DELETE FROM purchases"))
                conn.commit()
                print("✓ Tabela zerada (user_id não pode ser convertido para UUID)")
                
                # Passo 3: Tornar auth_id NOT NULL
                conn.execute(text("ALTER TABLE purchases ALTER COLUMN auth_id SET NOT NULL"))
                conn.commit()
                print("✓ Coluna auth_id definida como NOT NULL")
                
                # Passo 4: Recriar índice
                conn.execute(text("DROP INDEX IF EXISTS ix_purchases_user_id"))
                conn.execute(text("CREATE INDEX ix_purchases_auth_id ON purchases(auth_id)"))
                conn.commit()
                print("✓ Índice criado em auth_id")
                
                # Passo 5: Remover coluna user_id
                conn.execute(text("ALTER TABLE purchases DROP COLUMN user_id"))
                conn.commit()
                print("✓ Coluna user_id removida")
                
            print("\n✓ Migração concluída com sucesso!")
            return True
        else:
            print("\nAVISO: Coluna user_id não encontrada.")
            print("Parece que a tabela já foi migrada ou está em um estado diferente.")
            return True
            
    except Exception as e:
        print(f"\n✗ ERRO durante migração: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()
        engine.dispose()

if __name__ == '__main__':
    print("=" * 60)
    print("Migração: user_id → auth_id")
    print("=" * 60)
    
    success = migrate_database()
    
    if success:
        print("\n" + "=" * 60)
        print("Migração concluída!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("Migração falhou!")
        print("=" * 60)
        sys.exit(1)