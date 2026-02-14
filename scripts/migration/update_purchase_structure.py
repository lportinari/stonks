"""
Migração para atualizar a estrutura da tabela purchases no PostgreSQL:
- Alterar ticker de VARCHAR(10) para VARCHAR(50)
- Alterar quantidade de INTEGER para DOUBLE PRECISION
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.database import engine, SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Executa a migração do banco de dados PostgreSQL"""
    try:
        with engine.connect() as conn:
            # Iniciar transação
            trans = conn.begin()
            
            logger.info("Iniciando migração da tabela purchases...")
            
            # Verificar se a tabela existe
            check_table = text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'purchases'
            """)
            result = conn.execute(check_table).fetchone()
            
            if not result:
                logger.error("Tabela 'purchases' não encontrada!")
                return False
            
            # Obter estrutura atual da tabela
            current_schema = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'purchases'
                ORDER BY ordinal_position
            """)).fetchall()
            
            logger.info("Estrutura atual da tabela:")
            for col in current_schema:
                logger.info(f"  {col[0]}: {col[1]}({col[2] if col[2] else ''})")
            
            # Verificar se já foi migrado
            ticker_migrated = False
            qtd_migrated = False
            
            for col in current_schema:
                if col[0] == 'ticker':
                    ticker_migrated = (col[2] == 50) if col[2] else False
                elif col[0] == 'quantidade':
                    qtd_migrated = 'double' in col[1].lower() if col[1] else False
            
            if ticker_migrated:
                logger.info("Ticker já está com VARCHAR(50)")
            
            if qtd_migrated:
                logger.info("Quantidade já está com DOUBLE PRECISION")
                
            if ticker_migrated and qtd_migrated:
                logger.info("Migração já aplicada anteriormente!")
                trans.commit()
                return True
            
            # Alterar tipo da coluna quantidade
            logger.info("Alterando quantidade de INTEGER para DOUBLE PRECISION...")
            conn.execute(text("""
                ALTER TABLE purchases 
                ALTER COLUMN quantidade TYPE DOUBLE PRECISION
            """))
            
            # Alterar tipo da coluna ticker
            logger.info("Alterando ticker de VARCHAR(10) para VARCHAR(50)...")
            conn.execute(text("""
                ALTER TABLE purchases 
                ALTER COLUMN ticker TYPE VARCHAR(50)
            """))
            
            # Confirmar transação
            trans.commit()
            
            # Verificar estrutura atualizada
            logger.info("✅ Migração concluída com sucesso!")
            logger.info("Estrutura atualizada:")
            updated_schema = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'purchases'
                ORDER BY ordinal_position
            """)).fetchall()
            
            for col in updated_schema:
                logger.info(f"  {col[0]}: {col[1]}({col[2] if col[2] else ''})")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro durante a migração: {e}")
        if 'trans' in locals():
            trans.rollback()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRAÇÃO: Atualizar estrutura da tabela purchases")
    print("(PostgreSQL)")
    print("=" * 60)
    print()
    print("Esta migração vai:")
    print("  1. Alterar ticker de VARCHAR(10) para VARCHAR(50)")
    print("  2. Alterar quantidade de INTEGER para DOUBLE PRECISION")
    print()
    
    resposta = input("Deseja continuar? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        sucesso = migrate()
        if sucesso:
            print("\n✅ Migração concluída!")
            sys.exit(0)
        else:
            print("\n❌ Migração falhou!")
            sys.exit(1)
    else:
        print("\nMigração cancelada.")
        sys.exit(0)
