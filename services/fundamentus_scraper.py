import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict, Optional
import logging
from config import Config

logger = logging.getLogger(__name__)

class FundamentusScraper:
    """Classe responsável por extrair dados do site Fundamentus"""
    
    def __init__(self):
        self.base_url = Config.FUNDAMENTUS_URL
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_stocks_data(self) -> List[Dict]:
        """
        Extrai dados de todas as ações do site Fundamentus
        
        Returns:
            List[Dict]: Lista de dicionários com dados das ações
        """
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'resultado'})
            
            if not table:
                logger.error("Tabela de resultados não encontrada")
                return []
            
            # Extrair dados da tabela
            rows = table.find_all('tr')[1:]  # Pular cabeçalho
            
            stocks_data = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 20:  # Verificar se temos colunas suficientes
                    try:
                        stock_data = self._parse_stock_row(cols)
                        if stock_data:
                            stocks_data.append(stock_data)
                    except Exception as e:
                        logger.warning(f"Erro ao processar linha: {e}")
                        continue
            
            logger.info(f"Extraídos dados de {len(stocks_data)} ações")
            return stocks_data
            
        except requests.RequestException as e:
            logger.error(f"Erro na requisição ao Fundamentus: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado no scraping: {e}")
            return []
    
    def _parse_stock_row(self, cols) -> Optional[Dict]:
        """
        Processa uma linha da tabela e converte para dicionário
        
        Args:
            cols: Lista de colunas da tabela
            
        Returns:
            Dict: Dicionário com dados da ação ou None se inválido
        """
        def safe_float(value):
            """Converte valor para float de forma segura"""
            if value.strip() in ['-', '', '0']:
                return None
            try:
                # Remover formatação brasileira (ponto como milhar, vírgula como decimal)
                cleaned = value.replace('.', '').replace(',', '.')
                return float(cleaned)
            except (ValueError, AttributeError):
                return None
        
        def safe_percent(value):
            """Converte percentual para float"""
            if value.strip() in ['-', '', '0']:
                return None
            try:
                # Remover % e converter
                cleaned = value.replace('%', '').replace('.', '').replace(',', '.')
                return float(cleaned) / 100
            except (ValueError, AttributeError):
                return None
        
        try:
            # Mapeamento das colunas conforme o layout do Fundamentus
            data = {
                'ticker': cols[0].text.strip().split(' ')[0],  # Pega só o ticker
                'empresa': cols[0].text.strip(),
                'setor': cols[1].text.strip() if len(cols) > 1 else None,
                'subsetor': cols[2].text.strip() if len(cols) > 2 else None,
                'cotacao': safe_float(cols[3].text),
                'pl': safe_float(cols[4].text),
                'pvp': safe_float(cols[5].text),
                'psr': safe_float(cols[6].text),
                'div_yield': safe_percent(cols[7].text),
                'p_ativo': safe_float(cols[8].text),
                'p_cap_giro': safe_float(cols[9].text),
                'p_ebit': safe_float(cols[10].text),
                'p_ativ_circ_liq': safe_float(cols[11].text),
                'ev_ebit': safe_float(cols[12].text),
                'ev_ebitda': safe_float(cols[13].text),
                'mrg_ebit': safe_percent(cols[14].text),
                'mrg_liq': safe_percent(cols[15].text),
                'liquidez_corr': safe_float(cols[16].text),
                'roic': safe_percent(cols[17].text),
                'roe': safe_percent(cols[18].text),
                'liquidez_2m': safe_float(cols[19].text),
                'patr_ativ': safe_float(cols[20].text),
                'passivo_ativ': safe_float(cols[21].text),
                'giro_ativos': safe_float(cols[22].text),
                'cota_ativos': safe_float(cols[23].text),
                
                # Campos adicionais que podemos precisar
                'div_bruta_patrim': None,  # Não disponível diretamente no Fundamentus
                'div_liquida_patrim': None,
                'div_liquida_ebitda': None,
                'cresc_receita_5a': None,
                'cresc_lucro_5a': None,
                
                'valor_mercado': None,  # Precisa ser calculado
                'patrimonio_liquido': None,
            }
            
            # Filtrar ações sem cotação ou dados básicos
            if not data['cotacao'] or not data['ticker']:
                return None
                
            return data
            
        except Exception as e:
            logger.warning(f"Erro ao parsear dados da ação: {e}")
            return None
    
    def get_stock_detail(self, ticker: str) -> Optional[Dict]:
        """
        Obtém dados detalhados de uma ação específica
        
        Args:
            ticker: Ticker da ação (ex: PETR4)
            
        Returns:
            Dict: Dados detalhados da ação ou None
        """
        try:
            detail_url = f'https://www.fundamentus.com.br/detalhes.php?papel={ticker}'
            response = requests.get(detail_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair dados da página de detalhes
            # Esta é uma implementação básica - pode ser expandida
            data = {'ticker': ticker}
            
            # Aqui poderíamos extrair mais dados específicos da página de detalhes
            # Por ora, mantemos simples
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes de {ticker}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Testa se a conexão com o Fundamentus está funcionando"""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False