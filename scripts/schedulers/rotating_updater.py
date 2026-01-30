#!/usr/bin/env python3
"""
Sistema de Atualização Rotativa de Ações
Atualiza diferentes lotes de ações a cada execução sem depender de APIs externas para listagem
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict
import sys

from services.professional_apis import ProfessionalAPIService
from get_real_quotes import get_real_quote
from models.database import SessionLocal
from models.stock import Stock
from services.ranking_service import RankingService
from services.cache_manager import CacheManager

class RotatingUpdater:
    """Sistema de atualização com rotação inteligente de ações"""
    
    def __init__(self):
        self.api_service = ProfessionalAPIService()
        
        # Lista extendida de ações da B3 (top 100+ por liquidez)
        self.all_b3_stocks = [
            # Top 50 (maior liquidez)
            'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
            'MGLU3', 'B3SA3', 'BRFS3', 'ABEV3', 'BPAC11',
            'ITSA4', 'SULA11', 'RAIL3', 'GGBR4', 'SUZB3',
            'CYRE3', 'EQTL3', 'RENT3', 'CVCB3', 'LREN3',
            'VIVT3', 'TIMS3', 'BBAS3', 'SANB11', 'CCRO3',
            'CSAN3', 'KLBN11', 'HYPE3', 'JBSS3', 'MRFG3',
            'COGN3', 'ENBR3', 'ELET3', 'RADL3', 'TOTS3',
            'YDUQ3', 'PRIO3', 'GOLL4', 'EMBR3', 'NTCO3',
            'PCAR3', 'CRFB3', 'IGTI11', 'SQIA3', 'SMFT3',
            
            # Ações médias
            'CIEL3', 'LWSA3', 'MDIA3', 'EZTC3', 'GRND3',
            'RRRP3', 'BIDI11', 'BOVA11', 'SMAL11', 'IVVB11',
            'QUAL3', 'USIM5', 'GOAU4', 'CSNA3', 'BRAP4',
            'GNDI3', 'TGMA3', 'CMIG4', 'CPLE6', 'SAPR4',
            'EQTL3', 'CEAB3', 'VIVA3', 'TCSA3', 'LAME4',
            'CRPG5', 'LEVE3', 'PTNT4', 'DTEX3', 'BRKM5',
            'CAMB3', 'ENEV3', 'BRML3', 'MNPR3', 'MYPK3',
            'ELET6', 'CGAS5', 'JHSF3', 'JSLG3', 'MRVE3',
            
            # BDRs e outros
            'AAPL34', 'MSFT34', 'GOOGL34', 'AMZO34', 'TSLA34',
            'BACN34', 'NVDA34', 'META34', 'DISB34', 'NFLX34',
            'WEGE3', 'RAIZ4', 'FRAS3', 'JFEN3', 'KEPL3'
        ]
        
        # Adicionar ações existentes no banco
        self.add_existing_stocks_from_db()
        
        # Remover duplicatas
        self.all_b3_stocks = list(set(self.all_b3_stocks))
        self.all_b3_stocks.sort()
        
        print(f"Sistema inicializado com {len(self.all_b3_stocks)} acoes disponiveis")
    
    def add_existing_stocks_from_db(self):
        """Adiciona ações que já existem no banco"""
        try:
            session = SessionLocal()
            existing_stocks = session.query(Stock).all()
            
            for stock in existing_stocks:
                if stock.ticker and stock.ticker not in self.all_b3_stocks:
                    self.all_b3_stocks.append(stock.ticker)
            
            session.close()
            print(f"Adicionadas {len(existing_stocks)} acoes existentes do banco")
            
        except Exception as e:
            print(f"Erro ao adicionar acoes do banco: {e}")
    
    def get_recently_updated(self, hours: int = 2) -> List[str]:
        """Obtém ações atualizadas recentemente"""
        try:
            session = SessionLocal()
            recent_threshold = datetime.now() - timedelta(hours=hours)
            
            recent_stocks = session.query(Stock).filter(
                Stock.data_atualizacao >= recent_threshold
            ).all()
            
            recent_tickers = [s.ticker for s in recent_stocks]
            session.close()
            
            return recent_tickers
            
        except Exception as e:
            print(f"Erro ao obter atualizacoes recentes: {e}")
            return []
    
    def get_rotated_batch(self, batch_size: int = 20, exclude_recent: bool = True) -> List[str]:
        """Gera lote rotacionado de ações"""
        available_stocks = self.all_b3_stocks.copy()
        
        # Excluir recentes se solicitado
        if exclude_recent:
            recent_tickers = self.get_recently_updated(hours=2)
            exclude_set = set(recent_tickers)
            available_stocks = [s for s in available_stocks if s not in exclude_set]
            
            print(f"Excluidas {len(recent_tickers)} acoes recentes")
        
        # Embaralhar para rotação
        random.shuffle(available_stocks)
        
        # Retornar lote
        batch = available_stocks[:batch_size]
        
        print(f"LOTE GERADO: {len(batch)}/{len(available_stocks)} acoes disponiveis")
        
        return batch
    
    def get_priority_batch(self) -> List[str]:
        """Retorna lote de ações prioritárias (top liquidez)"""
        priority_stocks = [
            'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
            'MGLU3', 'B3SA3', 'BRFS3', 'ABEV3', 'BPAC11',
            'ITSA4', 'SULA11', 'RAIL3', 'GGBR4', 'SUZB3'
        ]
        
        # Filtrar apenas as que existem em nossa lista
        available_priority = [s for s in priority_stocks if s in self.all_b3_stocks]
        
        print(f"LOTE PRIORITARIO: {len(available_priority)} acoes")
        return available_priority
    
    def get_random_sample(self, sample_size: int = 30) -> List[str]:
        """Retorna amostra aleatória de ações"""
        sample = random.sample(self.all_b3_stocks, min(sample_size, len(self.all_b3_stocks)))
        
        print(f"AMOSTRA ALEATORIA: {len(sample)} acoes")
        return sample
    
    def update_batch(self, tickers: List[str]) -> Dict:
        """Atualiza um lote de ações"""
        print(f"ATUALIZANDO LOTE: {len(tickers)} acoes")
        print("=" * 60)
        
        results = {}
        session = SessionLocal()
        
        try:
            for i, ticker in enumerate(tickers, 1):
                print(f"[{i:2d}/{len(tickers)}] {ticker}...")
                
                try:
                    # Tentar APIs profissionais primeiro
                    data = self.api_service.get_professional_data(ticker)
                    
                    if not data or not data.get('success'):
                        # Fallback para web scraping
                        data = get_real_quote(ticker)
                    
                    if data and data.get('success') and data.get('cotacao'):
                        # Atualizar no banco
                        stock = session.query(Stock).filter(Stock.ticker == ticker).first()
                        
                        if stock:
                            old_price = stock.cotacao
                            stock.cotacao = data['cotacao']
                            stock.fonte_dados = data['fonte_dados']
                            
                            # Converter data se necessário
                            if isinstance(data['data_atualizacao'], str):
                                stock.data_atualizacao = datetime.fromisoformat(data['data_atualizacao'].replace('Z', '+00:00'))
                            else:
                                stock.data_atualizacao = data['data_atualizacao']
                            
                            # Atualizar indicadores se disponíveis
                            for field in ['div_yield', 'pl', 'pvp', 'roe', 'margem_liquida', 
                                        'ev_ebitda', 'psr', 'liquidez_corrente', 'setor', 'subsetor']:
                                if data.get(field):
                                    setattr(stock, field, data[field])
                            
                            change = data['cotacao'] - old_price if old_price else 0
                            change_percent = (change / old_price * 100) if old_price and old_price > 0 else 0
                            
                            print(f"    OK: R$ {old_price:.2f} -> R$ {data['cotacao']:.2f} ({change_percent:+.1f}%) [{data['fonte_dados']}]")
                            
                            results[ticker] = {
                                'success': True,
                                'old_price': old_price,
                                'new_price': data['cotacao'],
                                'source': data['fonte_dados']
                            }
                        else:
                            # Criar nova ação se não existir
                            print(f"    CRIANDO nova acao {ticker}")
                            new_stock = Stock(
                                ticker=ticker,
                                cotacao=data['cotacao'],
                                fonte_dados=data['fonte_dados'],
                                data_atualizacao=datetime.fromisoformat(data['data_atualizacao'].replace('Z', '+00:00'))
                            )
                            
                            # Adicionar indicadores se disponíveis
                            for field in ['div_yield', 'pl', 'pvp', 'roe', 'margem_liquida', 
                                        'ev_ebitda', 'psr', 'liquidez_corrente', 'setor', 'subsetor']:
                                if data.get(field):
                                    setattr(new_stock, field, data[field])
                            
                            session.add(new_stock)
                            
                            results[ticker] = {
                                'success': True,
                                'old_price': 0,
                                'new_price': data['cotacao'],
                                'source': data['fonte_dados'],
                                'created': True
                            }
                    else:
                        print(f"    FALHA: Sem dados obtidos")
                        results[ticker] = {'success': False, 'reason': 'no_data'}
                
                except Exception as e:
                    print(f"    ERRO: {e}")
                    results[ticker] = {'success': False, 'reason': str(e)}
                
                # Delay entre ações
                if i < len(tickers):
                    time.sleep(3)  # 3 segundos entre ações
            
            # Commit das alterações
            session.commit()
            
            # Recalcular scores se houve atualizações
            successful_updates = [ticker for ticker, result in results.items() if result.get('success')]
            if successful_updates:
                print(f"\nRecalculando scores para {len(successful_updates)} acoes atualizadas...")
                ranking_service = RankingService()
                cache_manager = CacheManager()
                ranking_service.update_ranking()
                cache_manager.clear_all()
            
            # Resumo
            successful = len(successful_updates)
            print(f"\nRESUMO: {successful}/{len(tickers)} acoes atualizadas com sucesso")
            
            return results
            
        except Exception as e:
            session.rollback()
            print(f"ERRO NO LOTE: {e}")
            return {}
        finally:
            session.close()
    
    def update_priority_stocks(self) -> Dict:
        """Atualiza ações prioritárias"""
        priority_batch = self.get_priority_batch()
        return self.update_batch(priority_batch)
    
    def update_rotated_batch(self, batch_size: int = 20) -> Dict:
        """Atualiza lote rotacionado"""
        rotated_batch = self.get_rotated_batch(batch_size)
        return self.update_batch(rotated_batch)
    
    def update_random_batch(self, sample_size: int = 30) -> Dict:
        """Atualiza amostra aleatória"""
        random_batch = self.get_random_sample(sample_size)
        return self.update_batch(random_batch)
    
    def get_status(self) -> Dict:
        """Retorna status do sistema"""
        try:
            session = SessionLocal()
            
            # Total de ações no banco
            total_stocks = session.query(Stock).count()
            
            # Ações atualizadas recentemente
            recent_2h = self.get_recently_updated(hours=2)
            recent_24h = self.get_recently_updated(hours=24)
            
            # Fontes de dados
            all_stocks = session.query(Stock).all()
            sources = {}
            for stock in all_stocks:
                source = stock.fonte_dados or 'unknown'
                sources[source] = sources.get(source, 0) + 1
            
            session.close()
            
            return {
                'total_stocks': total_stocks,
                'available_stocks': len(self.all_b3_stocks),
                'recent_2h': len(recent_2h),
                'recent_24h': len(recent_24h),
                'sources': sources
            }
            
        except Exception as e:
            print(f"Erro ao obter status: {e}")
            return {}

def main():
    """Função principal"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        updater = RotatingUpdater()
        
        if command == "priority":
            print("ATUALIZANDO ACOES PRIORITARIAS")
            print("=" * 60)
            results = updater.update_priority_stocks()
            
        elif command == "rotate":
            batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            print(f"ATUALIZANDO LOTE ROTACIONADO ({batch_size} acoes)")
            print("=" * 60)
            results = updater.update_rotated_batch(batch_size)
            
        elif command == "random":
            sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            print(f"ATUALIZANDO AMOSTRA ALEATORIA ({sample_size} acoes)")
            print("=" * 60)
            results = updater.update_random_batch(sample_size)
            
        elif command == "status":
            print("STATUS DO SISTEMA ROTATIVO")
            print("=" * 60)
            status = updater.get_status()
            
            print(f"Acoes disponiveis: {status['available_stocks']}")
            print(f"Acoes no banco: {status['total_stocks']}")
            print(f"Atualizadas 2h: {status['recent_2h']}")
            print(f"Atualizadas 24h: {status['recent_24h']}")
            
            if status['sources']:
                print("\nFontes de dados:")
                for source, count in status['sources'].items():
                    print(f"  {source}: {count} acoes")
            
        else:
            print("Comandos disponíveis:")
            print("  python rotating_updater.py priority")
            print("  python rotating_updater.py rotate [tamanho]")
            print("  python rotating_updater.py random [tamanho]")
            print("  python rotating_updater.py status")
    else:
        print("Uso: python rotating_updater.py [priority|rotate|random|status]")

if __name__ == "__main__":
    main()