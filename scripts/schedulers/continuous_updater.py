#!/usr/bin/env python3
"""
Sistema Contínuo de Atualização com Rate Limiting Inteligente
Atualiza dados gradualmente para evitar bloqueios de APIs
"""

import time
import schedule
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import json

from services.professional_apis import ProfessionalAPIService
from get_real_quotes import get_real_quote
from models.database import SessionLocal
from models.stock import Stock
from services.ranking_service import RankingService
from services.cache_manager import CacheManager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_updater.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ContinuousUpdater:
    """Sistema contínuo de atualização com controle inteligente de rate limiting"""
    
    def __init__(self):
        self.api_service = ProfessionalAPIService()
        self.update_interval = 300  # 5 minutos entre atualizações
        self.batch_size = 3  # Ações por atualização (para respeitar rate limits)
        self.last_full_update = None
        
        # Lista completa de tickers
        self.all_tickers = [
            'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
            'GGBR4', 'ABEV3', 'MGLU3', 'B3SA3', 'BBAS3',
            'SANB11', 'RAIL3', 'SUZB3', 'KLBN11', 'LREN3',
            'RADL3', 'ELET3', 'ENBR3'
        ]
        
        # Prioridade de atualização (mais importantes primeiro)
        self.priority_tickers = [
            'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
            'GGBR4', 'ABEV3', 'MGLU3'
        ]
        
        # Estado interno
        self.current_index = 0
        self.update_queue = list(self.all_tickers)
        
        # Criar diretório de logs se não existir
        import os
        os.makedirs('logs', exist_ok=True)
    
    def update_single_stock(self, ticker: str) -> Dict:
        """Atualiza uma única ação com múltiplas fontes"""
        logger.info(f"Iniciando atualização de {ticker}")
        
        # Tentar APIs profissionais primeiro
        data = self.api_service.get_professional_data(ticker)
        
        if not data or not data.get('success'):
            # Fallback para web scraping
            logger.info(f"APIs profissionais falharam para {ticker}, tentando web scraping")
            data = get_real_quote(ticker)
        
        return data
    
    def update_batch_stocks(self, tickers: List[str]) -> Dict:
        """Atualiza um lote de ações de forma segura"""
        logger.info(f"Atualizando lote: {tickers}")
        
        results = {}
        session = SessionLocal()
        
        try:
            for ticker in tickers:
                try:
                    # Obter dados
                    data = self.update_single_stock(ticker)
                    
                    if data and data.get('success') and data.get('cotacao'):
                        # Atualizar no banco
                        stock = session.query(Stock).filter(Stock.ticker == ticker).first()
                        if stock:
                            old_price = stock.cotacao
                            stock.cotacao = data['cotacao']
                            stock.fonte_dados = data['fonte_dados']
                            # Converter string ISO para datetime
                            if isinstance(data['data_atualizacao'], str):
                                stock.data_atualizacao = datetime.fromisoformat(data['data_atualizacao'].replace('Z', '+00:00'))
                            else:
                                stock.data_atualizacao = data['data_atualizacao']
                            
                            # Atualizar indicadores se disponíveis
                            for field in ['div_yield', 'pl', 'pvp', 'roe', 'margem_liquida', 
                                        'ev_ebitda', 'psr', 'liquidez_corrente', 'setor', 'subsetor']:
                                if data.get(field):
                                    setattr(stock, field, data[field])
                            
                            results[ticker] = {
                                'success': True,
                                'old_price': old_price,
                                'new_price': data['cotacao'],
                                'source': data['fonte_dados']
                            }
                            
                            change = data['cotacao'] - old_price if old_price else 0
                            change_percent = (change / old_price * 100) if old_price and old_price > 0 else 0
                            
                            logger.info(f"{ticker}: R$ {old_price:.2f} → R$ {data['cotacao']:.2f} ({change_percent:+.1f}%) [{data['fonte_dados']}]")
                        else:
                            results[ticker] = {'success': False, 'reason': 'not_found_in_db'}
                            logger.warning(f"{ticker}: Não encontrada no banco de dados")
                    else:
                        results[ticker] = {'success': False, 'reason': 'no_data'}
                        logger.warning(f"{ticker}: Sem dados obtidos")
                
                except Exception as e:
                    results[ticker] = {'success': False, 'reason': str(e)}
                    logger.error(f"{ticker}: Erro na atualização - {e}")
                
                # Delay entre ações para respeitar rate limits
                time.sleep(5)  # 5 segundos entre ações
            
            # Commit das alterações
            session.commit()
            
            # Recalcular scores se houve atualizações
            successful_updates = [ticker for ticker, result in results.items() if result.get('success')]
            if successful_updates:
                logger.info(f"Recalculando scores para {len(successful_updates)} ações atualizadas")
                ranking_service = RankingService()
                cache_manager = CacheManager()
                ranking_service.update_ranking()
                cache_manager.clear_all()
            
            return results
            
        except Exception as e:
            session.rollback()
            logger.error(f"Erro no lote {tickers}: {e}")
            return {}
        finally:
            session.close()
    
    def get_next_batch(self) -> List[str]:
        """Obtém o próximo lote de ações para atualizar"""
        if not self.update_queue:
            self.update_queue = list(self.all_tickers)
        
        # Pegar próximas N ações
        batch = self.update_queue[:self.batch_size]
        self.update_queue = self.update_queue[self.batch_size:]
        
        return batch
    
    def update_priority_stocks(self) -> Dict:
        """Atualiza as ações prioritárias"""
        logger.info("Atualizando ações prioritárias")
        return self.update_batch_stocks(self.priority_tickers)
    
    def update_continuous_cycle(self) -> Dict:
        """Executa um ciclo contínuo de atualização"""
        batch = self.get_next_batch()
        
        if not batch:
            logger.info("Fila de atualização vazia, reiniciando ciclo")
            self.update_queue = list(self.all_tickers)
            batch = self.get_next_batch()
        
        return self.update_batch_stocks(batch)
    
    def run_full_update(self) -> Dict:
        """Executa atualização completa de todas as ações"""
        logger.info("Iniciando atualização completa de todas as ações")
        start_time = time.time()
        
        all_results = {}
        
        # Atualizar em lotes pequenos para respeitar rate limits
        for i in range(0, len(self.all_tickers), self.batch_size):
            batch = self.all_tickers[i:i + self.batch_size]
            logger.info(f"Processando lote {i//self.batch_size + 1}/{(len(self.all_tickers) + self.batch_size - 1)//self.batch_size}")
            
            batch_results = self.update_batch_stocks(batch)
            all_results.update(batch_results)
            
            # Delay maior entre lotes
            if i + self.batch_size < len(self.all_tickers):
                logger.info(f"Aguardando 60 segundos antes do próximo lote...")
                time.sleep(60)
        
        elapsed_time = time.time() - start_time
        successful = sum(1 for result in all_results.values() if result.get('success'))
        
        logger.info(f"Atualização completa concluída em {elapsed_time:.1f}s")
        logger.info(f"Sucesso: {successful}/{len(self.all_tickers)} ações")
        
        self.last_full_update = datetime.now()
        return all_results
    
    def start_scheduler(self):
        """Inicia o agendador automático"""
        logger.info("Iniciando agendador de atualizações contínuas")
        
        # Agenda: Prioritárias a cada 15 minutos
        schedule.every(15).minutes.do(self.update_priority_stocks)
        
        # Agenda: Ciclo contínuo a cada 30 minutos
        schedule.every(30).minutes.do(self.update_continuous_cycle)
        
        # Agenda: Atualização completa a cada 4 horas
        schedule.every(4).hours.do(self.run_full_update)
        
        # Executar uma vez no início
        self.update_priority_stocks()
        
        logger.info("Agendador iniciado. Pressione Ctrl+C para parar.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        except KeyboardInterrupt:
            logger.info("Agendador parado pelo usuário")
    
    def get_update_status(self) -> Dict:
        """Retorna status atual das atualizações"""
        session = SessionLocal()
        
        try:
            # Obter dados atualizados recentemente
            recent_threshold = datetime.now() - timedelta(hours=1)
            recent_stocks = session.query(Stock).filter(
                Stock.data_atualizacao >= recent_threshold
            ).all()
            
            # Agrupar por fonte
            sources = {}
            for stock in recent_stocks:
                source = stock.fonte_dados or 'unknown'
                sources[source] = sources.get(source, 0) + 1
            
            # Status geral
            total_stocks = session.query(Stock).count()
            recent_count = len(recent_stocks)
            
            return {
                'total_stocks': total_stocks,
                'recently_updated': recent_count,
                'update_percentage': (recent_count / total_stocks * 100) if total_stocks > 0 else 0,
                'sources': sources,
                'last_full_update': self.last_full_update.isoformat() if self.last_full_update else None,
                'queue_size': len(self.update_queue),
                'next_batch': self.update_queue[:self.batch_size] if self.update_queue else []
            }
            
        finally:
            session.close()

def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        updater = ContinuousUpdater()
        
        if command == "full":
            print("EXECUTANDO ATUALIZAÇÃO COMPLETA")
            print("=" * 50)
            results = updater.run_full_update()
            
            successful = sum(1 for result in results.values() if result.get('success'))
            print(f"\nRESULTADO: {successful}/{len(updater.all_tickers)} ações atualizadas")
            
        elif command == "priority":
            print("EXECUTANDO ATUALIZAÇÃO PRIORITÁRIA")
            print("=" * 50)
            results = updater.update_priority_stocks()
            
            successful = sum(1 for result in results.values() if result.get('success'))
            print(f"\nRESULTADO: {successful}/{len(updater.priority_tickers)} ações prioritárias atualizadas")
            
        elif command == "status":
            print("STATUS DAS ATUALIZAÇÕES")
            print("=" * 50)
            status = updater.get_update_status()
            
            print(f"Ações totais: {status['total_stocks']}")
            print(f"Atualizadas recentemente (1h): {status['recently_updated']}")
            print(f"Percentual atualizado: {status['update_percentage']:.1f}%")
            print(f"Última atualização completa: {status['last_full_update']}")
            print(f"Tamanho da fila: {status['queue_size']}")
            
            if status['sources']:
                print("\nFontes de dados recentes:")
                for source, count in status['sources'].items():
                    print(f"  {source}: {count} ações")
            
        elif command == "schedule":
            print("INICIANDO AGENDADOR CONTÍNUO")
            print("=" * 50)
            updater.start_scheduler()
            
        else:
            print("Comandos disponíveis:")
            print("  python continuous_updater.py full     - Atualização completa")
            print("  python continuous_updater.py priority - Ações prioritárias")
            print("  python continuous_updater.py status    - Status atual")
            print("  python continuous_updater.py schedule  - Iniciar agendador")
    else:
        print("Uso: python continuous_updater.py [full|priority|status|schedule]")

if __name__ == "__main__":
    main()