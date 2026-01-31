#!/usr/bin/env python3
"""
Script para recalcular todos os scores usando o novo sistema multi-classes
Este script vai atualizar todos os ativos no banco com scores específicos por classe
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
from services.ranking_service import RankingService
from services.asset_classifier import AssetClassifier
from models.database import SessionLocal
from models.stock import Stock

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Função principal para recalcular scores"""
    try:
        logger.info("Iniciando recálculo de scores com sistema multi-classes...")
        
        # Inicializar serviços
        ranking_service = RankingService()
        
        # Primeiro, classificar todos os ativos se necessário
        logger.info("Verificando classificação dos ativos...")
        with SessionLocal() as db:
            classifier = AssetClassifier(db)
            stocks = db.query(Stock).all()
            
            classificados = 0
            for stock in stocks:
                if not stock.asset_class:
                    stock.asset_class = classifier.classify_asset(stock.ticker)
                    classificados += 1
            
            if classificados > 0:
                db.commit()
                logger.info(f"Classificados {classificados} ativos")
        
        # Recalcular rankings
        logger.info("Recalculando rankings...")
        updated_count = ranking_service.update_ranking()
        
        logger.info(f"Ranking atualizado com sucesso! {updated_count} ativos processados")
        
        # Mostrar estatísticas finais
        stats = ranking_service.get_ranking_statistics()
        logger.info(f"Estatísticas finais: {stats['total_stocks']} ativos totais")
        logger.info(f"Score médio: {stats['avg_score']:.2f}")
        logger.info(f"Score máximo: {stats['top_score']:.2f}")
        
        # Contar por classe
        with SessionLocal() as db:
            class_counts = {}
            all_stocks = db.query(Stock).filter(Stock.cotacao > 0).all()
            
            for stock in all_stocks:
                cls = stock.asset_class or 'nao_classificado'
                class_counts[cls] = class_counts.get(cls, 0) + 1
            
            logger.info("Distribuição por classe:")
            for cls, count in class_counts.items():
                logger.info(f"  {cls}: {count} ativos")
        
        logger.info("Recálculo concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o recálculo: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())