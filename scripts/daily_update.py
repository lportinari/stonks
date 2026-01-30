#!/usr/bin/env python3
"""
Script de atualização diária dos dados das ações
Este script deve ser executado diariamente (via cron job ou task scheduler)
para atualizar os dados do Fundamentus e recalcular o ranking.
"""

import logging
import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hybrid_scraper import HybridScraper
from services.ranking_service import RankingService
from services.indicator_calculator import IndicatorCalculator
from services.cache_manager import CacheManager, CacheKeys
from models.database import SessionLocal
from models.stock import Stock
from sqlalchemy.orm import Session

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DailyUpdater:
    """Classe responsável pela atualização diária dos dados"""
    
    def __init__(self):
        self.scraper = HybridScraper()
        self.ranking_service = RankingService()
        self.calculator = IndicatorCalculator()
        self.cache_manager = CacheManager()
        
    def run_full_update(self):
        """Executa a atualização completa dos dados"""
        logger.info("Iniciando atualização diária dos dados...")
        
        try:
            # 1. Testar conexão com as fontes de dados
            if not self.scraper.test_connection():
                logger.error("Não foi possível conectar às fontes de dados")
                return False
            
            # 2. Coletar dados
            logger.info("Coletando dados das fontes híbridas...")
            stocks_data = self.scraper.get_stocks_data()
            
            if not stocks_data:
                logger.error("Nenhum dado foi coletado das fontes híbridas")
                return False
            
            logger.info(f"Dados de {len(stocks_data)} ações coletados")
            
            # 3. Salvar no banco de dados
            logger.info("Salvando dados no banco...")
            saved_count = self._save_to_database(stocks_data)
            
            if saved_count == 0:
                logger.error("Nenhuma ação foi salva no banco")
                return False
            
            # 4. Calcular scores e ranking
            logger.info("Calculando scores e ranking...")
            self._calculate_ranking()
            
            # 5. Limpar cache
            logger.info("Limpando cache...")
            self.cache_manager.clear_all()
            
            # 6. Gerar relatório
            self._generate_report(saved_count)
            
            logger.info("Atualização diária concluída com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro durante atualização diária: {e}")
            return False
    
    def _save_to_database(self, stocks_data):
        """Salva os dados coletados no banco de dados"""
        saved_count = 0
        
        with SessionLocal() as db:
            try:
                for stock_data in stocks_data:
                    # Verificar se a ação já existe
                    existing_stock = db.query(Stock).filter(
                        Stock.ticker == stock_data['ticker']
                    ).first()
                    
                    if existing_stock:
                        # Atualizar dados existentes
                        self._update_stock_data(existing_stock, stock_data)
                        existing_stock.data_atualizacao = datetime.now()
                        existing_stock.fonte_dados = stock_data.get('fonte_dados', 'hybrid')
                    else:
                        # Criar nova ação
                        new_stock = Stock()
                        self._update_stock_data(new_stock, stock_data)
                        new_stock.ticker = stock_data['ticker']
                        new_stock.fonte_dados = stock_data.get('fonte_dados', 'hybrid')
                        db.add(new_stock)
                    
                    saved_count += 1
                
                db.commit()
                logger.info(f"{saved_count} ações salvas/atualizadas no banco")
                
            except Exception as e:
                db.rollback()
                logger.error(f"Erro ao salvar no banco: {e}")
                raise
        
        return saved_count
    
    def _update_stock_data(self, stock, stock_data):
        """Atualiza os dados de uma ação"""
        # Dados básicos
        stock.empresa = stock_data.get('empresa')
        stock.setor = stock_data.get('setor')
        stock.subsetor = stock_data.get('subsetor')
        stock.cotacao = stock_data.get('cotacao')
        
        # Indicadores de valuation
        stock.pl = stock_data.get('pl')
        stock.pvp = stock_data.get('pvp')
        stock.psr = stock_data.get('psr')
        stock.div_yield = stock_data.get('div_yield')
        stock.ev_ebit = stock_data.get('ev_ebit')
        stock.ev_ebitda = stock_data.get('ev_ebitda')
        
        # Indicadores de rentabilidade
        stock.roe = stock_data.get('roe')
        stock.roic = stock_data.get('roic')
        stock.margem_liquida = stock_data.get('mrg_liq')
        stock.margem_ebit = stock_data.get('mrg_ebit')
        
        # Outros indicadores
        stock.liquidity = stock_data.get('liquidez_corr')
        stock.giro_ativos = stock_data.get('giro_ativos')
    
    def _calculate_ranking(self):
        """Calcula os scores e posições do ranking"""
        with SessionLocal() as db:
            # Obter todas as ações
            stocks = db.query(Stock).all()
            
            # Calcular scores usando pesos padrão
            weights = self.calculator.indicator_limits = {
                'dy': 0.25,
                'pl': 0.20,
                'pvp': 0.20,
                'roe': 0.20,
                'margem_liquida': 0.15
            }
            
            calculated_count = 0
            for stock in stocks:
                stock_dict = stock.to_dict()
                score = self.calculator.calculate_stock_score(stock_dict, weights)
                
                if score is not None:
                    stock.score_final = score
                    calculated_count += 1
            
            # Commit dos scores
            db.commit()
            
            # Atualizar posições do ranking
            stocks_with_score = [s for s in stocks if s.score_final is not None]
            stocks_with_score.sort(key=lambda x: x.score_final, reverse=True)
            
            for i, stock in enumerate(stocks_with_score, 1):
                stock.rank_posicao = i
            
            db.commit()
            
            logger.info(f"Scores calculados para {calculated_count} ações")
    
    def _generate_report(self, saved_count):
        """Gera um relatório da atualização"""
        with SessionLocal() as db:
            total_stocks = db.query(Stock).count()
            stocks_with_score = db.query(Stock).filter(Stock.score_final.isnot(None)).count()
            
            report = f"""
========================================
RELATÓRIO DE ATUALIZAÇÃO DIÁRIA
========================================
Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Resumo:
- Ações coletadas: {saved_count}
- Total no banco: {total_stocks}
- Ações com score: {stocks_with_score}
- Taxa de sucesso: {(stocks_with_score/total_stocks*100):.1f}%

Top 5 Ações:
"""
            
            # Adicionar top 5 ao relatório
            top_stocks = db.query(Stock).filter(
                Stock.score_final.isnot(None)
            ).order_by(Stock.score_final.desc()).limit(5).all()
            
            for i, stock in enumerate(top_stocks, 1):
                report += f"{i}. {stock.ticker} - Score: {stock.score_final:.1f}\n"
            
            report += "========================================\n"
            
            # Salvar relatório
            with open(f"reports/update_report_{datetime.now().strftime('%Y%m%d')}.txt", 'w') as f:
                f.write(report)
            
            logger.info("Relatório gerado com sucesso")
            print(report)

def main():
    """Função principal"""
    logger.info("=" * 50)
    logger.info("INICIANDO ATUALIZAÇÃO DIÁRIA")
    logger.info("=" * 50)
    
    updater = DailyUpdater()
    success = updater.run_full_update()
    
    if success:
        logger.info("✅ Atualização diária concluída com sucesso!")
        sys.exit(0)
    else:
        logger.error("❌ Falha na atualização diária!")
        sys.exit(1)

if __name__ == "__main__":
    main()