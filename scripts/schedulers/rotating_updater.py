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
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.professional_apis import ProfessionalAPIService
from scripts.updaters.get_real_quotes import get_real_quote
from models.database import SessionLocal
from models.stock import Stock
from services.ranking_service import RankingService
from services.cache_manager import CacheManager

class RotatingUpdater:
    """Sistema de atualização com rotação inteligente de ações"""
    
    def __init__(self):
        self.api_service = ProfessionalAPIService()
        
        # Lista extendida de ações da B3 (Ibovespa + principais por liquidez)
        self.all_b3_stocks = [
            # IBOVESPA - Cartel Atual (2024)
            'PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3',
            'MGLU3', 'B3SA3', 'BRFS3', 'ABEV3', 'BPAC11',
            'ITSA4', 'SULA11', 'RAIL3', 'GGBR4', 'SUZB3',
            'CYRE3', 'EQTL3', 'RENT3', 'CVCB3', 'LREN3',
            'VIVT3', 'TIMS3', 'BBAS3', 'SANB11', 'CCRO3',
            'CSAN3', 'KLBN11', 'HYPE3', 'JBSS3', 'MRFG3',
            'COGN3', 'ENBR3', 'ELET3', 'RADL3', 'TOTS3',
            'YDUQ3', 'PRIO3', 'GOLL4', 'EMBR3', 'NTCO3',
            'PCAR3', 'CRFB3', 'IGTI11', 'SQIA3', 'SMFT3',
            'CIEL3', 'LWSA3', 'MDIA3', 'EZTC3', 'GRND3',
            'RRRP3', 'BIDI11', 'BOVA11', 'SMAL11', 'IVVB11',
            'QUAL3', 'USIM5', 'GOAU4', 'CSNA3', 'BRAP4',
            'GNDI3', 'TGMA3', 'CMIG4', 'CPLE6', 'SAPR4',
            'EQTL3', 'CEAB3', 'VIVA3', 'TCSA3', 'LAME4',
            'CRPG5', 'LEVE3', 'PTNT4', 'DTEX3', 'BRKM5',
            'CAMB3', 'ENEV3', 'BRML3', 'MNPR3', 'MYPK3',
            'ELET6', 'CGAS5', 'JHSF3', 'JSLG3', 'MRVE3',
            
            # Ações de Alto Volume e Setores Chave
            'PETR3', 'VALE5', 'ITUB3', 'BBDC3', 'WEGE4',
            'MGLU4', 'B3SA4', 'BRFS4', 'ABEV4', 'BPAC12',
            'ITSA3', 'SULA12', 'RAIL4', 'GGBR3', 'SUZB4',
            'CYRE4', 'EQTL4', 'RENT4', 'CVCB4', 'LREN4',
            'VIVT4', 'TIMS4', 'BBAS4', 'SANB12', 'CCRO4',
            'CSAN4', 'KLBN12', 'HYPE4', 'JBSS4', 'MRFG4',
            'COGN4', 'ENBR4', 'ELET4', 'RADL4', 'TOTS4',
            'YDUQ4', 'PRIO4', 'GOLL3', 'EMBR4', 'NTCO4',
            'PCAR4', 'CRFB4', 'IGTI12', 'SQIA4', 'SMFT4',
            
            # Setor Bancário e Financeiro
            'BAU4', 'BBSE3', 'BEEF3', 'BPAN4', 'BRSR6',
            'CAGR3', 'CASH3', 'CI3', 'CIEL4', 'CXSE3',
            'DIAS3', 'DIRR3', 'ECOR3', 'EGIE3', 'ELE3',
            'ELET6', 'ENAT3', 'ENGI11', 'ENGI4', 'EQTL3',
            'ESTR3', 'EVEN3', 'FESA4', 'FHER3', 'FRAS3',
            'GEPA4', 'GGBR4', 'GOAU4', 'GPI4', 'GRND3',
            'GSHP3', 'HGTX3', 'HGLG11', 'HYPE3', 'IGBR3',
            
            # Setor de Energia
            'CMIG4', 'CMIN3', 'COCE5', 'CPFE3', 'CPLE6',
            'CRPG5', 'CSMG3', 'CSNA3', 'CVCB3', 'CYRE3',
            'DAMT3', 'DASA3', 'DTEX3', 'ECOR3', 'ELET3',
            'ELET6', 'ELPL3', 'EMBR3', 'ENBR3', 'ENEV3',
            'ENGI11', 'ENGI3', 'ENJU3', 'EQTL3', 'ESTR3',
            'EVEN3', 'EZTC3', 'FESA3', 'FHER3', 'FLRY3',
            
            # Setor de Consumo e Varejo
            'AMER3', 'ARZZ3', 'BEEF3', 'BGIP4', 'BOBR4',
            'BOVA11', 'BPAC11', 'BRAP4', 'BRDT3', 'BRFS3',
            'BRKM5', 'BRML3', 'BRSR6', 'BSEV3', 'CAML3',
            'CAMB4', 'CARD3', 'CASH3', 'CCRO3', 'CCXR3',
            'CEAB3', 'CESP6', 'CGRW4', 'CGRA4', 'CIEL3',
            
            # Setor Industrial e Construção
            'CRFB3', 'CSAN3', 'CSNA3', 'CVCB3', 'CYRE3',
            'DASA3', 'DCTH4', 'DIRR3', 'DXCO3', 'ECOR3',
            'ELET3', 'ELET6', 'ELPL4', 'EMBR3', 'ENBR3',
            'ENEV3', 'EQTL3', 'ESTR3', 'EVEN3', 'EZTC3',
            'FESA3', 'FHER3', 'FLRY3', 'FRAS3', 'GFSA3',
            'GGBR4', 'GOAU4', 'GOLL4', 'GPRI3', 'GRND3',
            'GSHP3', 'HGTX3', 'HGLG11', 'HYPE3', 'IGBR3',
            
            # Fundos e ETFs
            'BOVA11', 'BRAX11', 'BRCR11', 'ECOO11', 'ETFI11',
            'FIND11', 'FIVN11', 'FRIO3', 'HASH11', 'HGBS11',
            'HGLG11', 'HGRE11', 'HGPO11', 'HGRU11', 'HYCB11',
            'IBOV11', 'IFRA11', 'IMAB11', 'IVVB11', 'KNCR11',
            'KNRI11', 'KOCH11', 'LCAM11', 'LGPD11', 'LOVB11',
            'MALL11', 'MCHF11', 'MCRI11', 'MGFF11', 'MHAG11',
            'MXRF11', 'NEOE3', 'NGRD11', 'OUCY11', 'PABY4',
            'PARD11', 'PATI3', 'PBOV11', 'PCAR3', 'PDTC3',
            'PINE4', 'POMO4', 'PORT3', 'POSI3', 'PRIO3',
            'PTBL11', 'QGEP11', 'RAIL3', 'RAIL4', 'RBED11',
            'RCEF11', 'RCFA11', 'RDPD4', 'RDRD3', 'RECV11',
            'RENT3', 'RENT4', 'RNGO11', 'RPDA5', 'RRPI3',
            'RSID4', 'SAPR11', 'SAPR3', 'SAPR4', 'SBFG3',
            'SBSI3', 'SCAR3', 'SEER3', 'SLED4', 'SMAL11',
            'SMAN11', 'SMTO3', 'SNSL5', 'SPXI11', 'SQIA3',
            'STBP11', 'SULA11', 'SULA12', 'SUZB3', 'SUZB4',
            'TAEE11', 'TCNN4', 'TECN3', 'TEKA3', 'TELB3',
            'TELB4', 'TEND3', 'TETR4', 'TGMA3', 'TIMP3',
            'TOTS3', 'TRIS3', 'TRPL4', 'TSPP4', 'UCAS3',
            'UGPA3', 'UNIP6', 'UNIP7', 'USIM5', 'VALE3',
            'VALE5', 'VAMO3', 'VBRF3', 'VCRE3', 'VIIA3',
            'VIVR3', 'VIVT3', 'VIVT4', 'VLID3', 'VULC3',
            'WEGE3', 'WEGE4', 'WIZS3', 'WIZT3', 'WHRL4',
            'WSON33', 'YDUQ3', 'YDUQ4', 'ZZBR3', 'ZZBR4',
            
            # BDRs - Ações Internacionais
            'AAPL34', 'MSFT34', 'GOOGL34', 'AMZO34', 'TSLA34',
            'BACN34', 'NVDA34', 'META34', 'DISB34', 'NFLX34',
            'PYPL34', 'TXR34', 'MELI34', 'NTCO3', 'NTCO4',
            'AZUL4', 'BAU3', 'BEEF3', 'BIDI11', 'BIDI4',
            'BPAN4', 'BRSR6', 'CAML3', 'CARD3', 'CASH3',
            'CCRO3', 'CEPE3', 'CEPE5', 'CEPE6', 'CGAS3',
            'CGAS4', 'CGAS5', 'CGRA3', 'CGRA4', 'CMLH3',
            'CNTO3', 'COCE3', 'COCE4', 'COCE5', 'COCE6',
            'CPGD6', 'CRDE3', 'CRDE5', 'CRDE6', 'CREG3',
            'CREG4', 'CREG5', 'CREG6', 'CRFB3', 'CRFB4',
            'CRPG3', 'CRPG4', 'CRPG5', 'CRPG6', 'CSAN3',
            'CSAN4', 'CSAN5', 'CSAN6', 'CSED3', 'CSRN3',
            'CSRN5', 'CSRN6', 'CSTM3', 'CTKA3', 'CTKA4',
            'CTNM3', 'CTNM4', 'CTNP3', 'CTNP4', 'CTSA3',
            'CTSA4', 'CXP4', 'CXP5', 'CYRE3', 'CYRE4',
            'CYRE5', 'CYRE6', 'CYSR3', 'DAGB33', 'DAIH3',
            'DASA3', 'DASA4', 'DATA3', 'DCTH4', 'DESK3',
            'DHGB3', 'DHHG3', 'DIAS3', 'DIMA3', 'DIRR3',
            'DISB34', 'DMMO3', 'DTEX3', 'DTEX4', 'DUQF3'
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
                    # Usar apenas BrAPI
                    data = self.api_service.get_from_brapi(ticker)
                    
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
                            
                            # Mapear todos os campos da BrAPI para o modelo (exceto datas)
                            field_mapping = {
                                # Campos básicos
                                'cotacao': 'cotacao',
                                'empresa': 'empresa',
                                'short_name': 'short_name',
                                'setor': 'setor',
                                'subsetor': 'subsetor',
                                'currency': 'currency',
                                'logo_url': 'logo_url',
                                
                                # Variação e preços diários
                                'regular_market_day_high': 'regular_market_day_high',
                                'regular_market_day_low': 'regular_market_day_low',
                                'regular_market_day_range': 'regular_market_day_range',
                                'regular_market_change': 'regular_market_change',
                                'regular_market_change_percent': 'regular_market_change_percent',
                                'regular_market_previous_close': 'regular_market_previous_close',
                                'regular_market_open': 'regular_market_open',
                                
                                # Dados de 52 semanas
                                'fifty_two_week_range': 'fifty_two_week_range',
                                'fifty_two_week_low': 'fifty_two_week_low',
                                'fifty_two_week_high': 'fifty_two_week_high',
                                
                                # Métricas adicionais
                                'price_earnings': 'price_earnings',
                                'earnings_per_share': 'earnings_per_share',
                                
                                # Indicadores fundamentais
                                'div_yield': 'div_yield',
                                'pl': 'pl',
                                'pvp': 'pvp',
                                'roe': 'roe',
                                'margem_liquida': 'margem_liquida',
                                'ev_ebitda': 'ev_ebitda',
                                'psr': 'psr',
                                'liquidez_corrente': 'liquidity',
                                'div_liquida_patrim': 'div_liquida_patrim',
                                'roic': 'roic',
                                'cresc_receita_5a': 'cresc_receita_5a',
                                
                                # Outros dados
                                'market_cap': 'valor_mercado',
                                'volume': 'volume'
                            }
                            
                            # Atualizar todos os indicadores disponíveis
                            for brapi_field, model_field in field_mapping.items():
                                if data.get(brapi_field) is not None:
                                    setattr(stock, model_field, data[brapi_field])
                            
                            # Tratar o campo de data separadamente
                            if data.get('regular_market_time'):
                                if isinstance(data['regular_market_time'], str):
                                    try:
                                        stock.regular_market_time = datetime.fromisoformat(data['regular_market_time'].replace('Z', '+00:00'))
                                    except:
                                        stock.regular_market_time = None  # Manter None se falhar
                                else:
                                    stock.regular_market_time = data['regular_market_time']
                            
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
                                empresa=ticker,  # Valor temporário
                                cotacao=data['cotacao'],
                                fonte_dados=data['fonte_dados'],
                                data_atualizacao=datetime.fromisoformat(data['data_atualizacao'].replace('Z', '+00:00'))
                            )
                            
                            # Adicionar indicadores se disponíveis
                            for field in ['div_yield', 'pl', 'pvp', 'roe', 'margem_liquida', 
                                        'ev_ebitda', 'psr', 'liquidez_corrente', 'setor', 'subsetor',
                                        'short_name', 'currency', 'logo_url']:
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
    
    def update_all_stocks(self) -> Dict:
        """Atualiza TODAS as ações disponíveis"""
        print("ATUALIZANDO TODAS AS AÇÕES DISPONÍVEIS")
        print("=" * 60)
        print(f"Total de ações para processar: {len(self.all_b3_stocks)}")
        print("=" * 60)
        
        all_results = {}
        batch_size = 20  # Processar em lotes para não sobrecarregar
        
        # Processar em lotes
        for i in range(0, len(self.all_b3_stocks), batch_size):
            batch = self.all_b3_stocks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(self.all_b3_stocks) + batch_size - 1) // batch_size
            
            print(f"\n=== PROCESSANDO LOTE {batch_num}/{total_batches} ===")
            print(f"Ações neste lote: {len(batch)}")
            
            batch_results = self.update_batch(batch)
            all_results.update(batch_results)
            
            # Delay maior entre lotes para respeitar rate limits
            if i + batch_size < len(self.all_b3_stocks):
                print(f"\nAguardando 60 segundos antes do próximo lote...")
                time.sleep(60)
        
        # Resumo final
        total_successful = sum(1 for result in all_results.values() if result.get('success'))
        total_processed = len(self.all_b3_stocks)
        
        print("\n" + "=" * 60)
        print("RESUMO FINAL - ATUALIZAÇÃO COMPLETA")
        print("=" * 60)
        print(f"Total processado: {total_processed} ações")
        print(f"Sucesso: {total_successful} ações")
        print(f"Falha: {total_processed - total_successful} ações")
        print(f"Taxa de sucesso: {(total_successful/total_processed*100):.1f}%")
        
        return all_results
    
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
            
        elif command == "all":
            print("ATUALIZANDO TODAS AS AÇÕES")
            print("=" * 60)
            results = updater.update_all_stocks()
            
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
            print("  python rotating_updater.py all          - ATUALIZA TODAS AS 350+ AÇÕES")
            print("  python rotating_updater.py status")
    else:
        print("Uso: python rotating_updater.py [priority|rotate|random|status]")

if __name__ == "__main__":
    main()