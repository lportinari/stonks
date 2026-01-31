#!/usr/bin/env python3
"""
Migration script para adicionar campo asset_class à tabela stocks
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from models.database import SessionLocal
from services.asset_classifier import AssetClassifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_asset_class_column():
    """Adiciona a coluna asset_class à tabela stocks"""
    session = SessionLocal()
    
    try:
        # Verificar se a coluna já existe
        result = session.execute(text("PRAGMA table_info(stocks)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'asset_class' in columns:
            logger.info("Coluna asset_class já existe")
            return
        
        # Adicionar a coluna
        logger.info("Adicionando coluna asset_class...")
        session.execute(text("""
            ALTER TABLE stocks 
            ADD COLUMN asset_class VARCHAR(20) DEFAULT 'acao'
        """))
        session.commit()
        logger.info("Coluna asset_class adicionada com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao adicionar coluna asset_class: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def populate_asset_class():
    """Popula o campo asset_class para todos os registros existentes"""
    session = SessionLocal()
    
    try:
        classifier = AssetClassifier(session)
        
        # Obter todos os registros sem asset_class
        result = session.execute(text("""
            SELECT id, ticker FROM stocks 
            WHERE asset_class IS NULL OR asset_class = 'acao'
        """))
        
        stocks_to_update = result.fetchall()
        logger.info(f"Processando {len(stocks_to_update)} registros...")
        
        updated_count = 0
        for stock_id, ticker in stocks_to_update:
            try:
                asset_class = classifier.classify_asset(ticker)
                session.execute(text("""
                    UPDATE stocks 
                    SET asset_class = :asset_class 
                    WHERE id = :stock_id
                """), {'asset_class': asset_class, 'stock_id': stock_id})
                
                updated_count += 1
                logger.debug(f"{ticker} -> {asset_class}")
                
            except Exception as e:
                logger.error(f"Erro ao classificar {ticker}: {e}")
        
        session.commit()
        logger.info(f"Classificação concluída. {updated_count} registros atualizados.")
        
    except Exception as e:
        logger.error(f"Erro ao popular asset_class: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def generate_classification_report():
    """Gera relatório final da classificação"""
    session = SessionLocal()
    
    try:
        result = session.execute(text("""
            SELECT asset_class, COUNT(*) as count 
            FROM stocks 
            GROUP BY asset_class 
            ORDER BY count DESC
        """))
        
        stats = result.fetchall()
        
        logger.info("\n" + "="*50)
        logger.info("RELATÓRIO DE CLASSIFICAÇÃO DE ATIVOS")
        logger.info("="*50)
        
        total = sum(row[1] for row in stats)
        
        for asset_class, count in stats:
            percentage = (count / total * 100) if total > 0 else 0
            logger.info(f"{asset_class.upper():10} : {count:3d} ({percentage:5.1f}%)")
        
        logger.info(f"{'TOTAL':10} : {total:3d} (100.0%)")
        
        # Exemplos por classe
        logger.info("\nEXEMPLOS POR CLASSE:")
        for asset_class, _ in stats:
            result = session.execute(text("""
                SELECT ticker FROM stocks 
                WHERE asset_class = :asset_class 
                LIMIT 5
            """), {'asset_class': asset_class})
            
            examples = [row[0] for row in result.fetchall()]
            logger.info(f"{asset_class.upper()}: {', '.join(examples)}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
    finally:
        session.close()

def main():
    """Função principal da migration"""
    logger.info("Iniciando migration para asset_class...")
    
    try:
        # Passo 1: Adicionar coluna
        add_asset_class_column()
        
        # Passo 2: Popular com classificação
        populate_asset_class()
        
        # Passo 3: Gerar relatório
        generate_classification_report()
        
        logger.info("\nMigration concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"Migration falhou: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()