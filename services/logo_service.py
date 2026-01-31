import requests
import logging
import os
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from models.stock import Stock
from services.professional_apis import ProfessionalAPIService
from config import Config

logger = logging.getLogger(__name__)

class LogoService:
    """Serviço responsável por obter e gerenciar logos das empresas"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.professional_api = ProfessionalAPIService()
        self.cache_dir = "database/cache/logos"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Garantir que o diretório de cache exista
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_logo_url(self, ticker: str, force_refresh: bool = False) -> Optional[str]:
        """
        Obtém URL do logo para um ticker, usando cache
        
        Args:
            ticker: Símbolo da ação
            force_refresh: Forçar atualização mesmo que tenha cache
            
        Returns:
            str: URL do logo ou None
        """
        cache_file = os.path.join(self.cache_dir, f"{ticker}.txt")
        
        # Verificar cache
        if not force_refresh and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_url = f.read().strip()
                    if cached_url and cached_url.startswith('http'):
                        logger.debug(f"Logo cache hit para {ticker}: {cached_url}")
                        return cached_url
            except Exception as e:
                logger.warning(f"Erro ao ler cache do logo para {ticker}: {e}")
        
        # Tentar obter da API profissional
        logo_url = self._get_logo_from_brapi(ticker)
        
        if logo_url:
            self._save_logo_cache(ticker, logo_url)
            return logo_url
        
        # Tentar outras fontes
        logo_url = self._get_logo_from_yahoo(ticker)
        if logo_url:
            self._save_logo_cache(ticker, logo_url)
            return logo_url
        
        # Tentar fontes alternativas
        logo_url = self._get_logo_alternative(ticker)
        if logo_url:
            self._save_logo_cache(ticker, logo_url)
            return logo_url
        
        logger.warning(f"Não foi possível obter logo para {ticker}")
        return None
    
    def _get_logo_from_brapi(self, ticker: str) -> Optional[str]:
        """Obtém logo da BrAPI"""
        try:
            data = self.professional_api.get_from_brapi(ticker)
            if data and data.get('logo_url'):
                logo_url = data['logo_url']
                if logo_url and logo_url.startswith('http'):
                    logger.debug(f"Logo obtido da BrAPI para {ticker}: {logo_url}")
                    return logo_url
        except Exception as e:
            logger.debug(f"Erro ao obter logo da BrAPI para {ticker}: {e}")
        
        return None
    
    def _get_logo_from_yahoo(self, ticker: str) -> Optional[str]:
        """Obtém logo do Yahoo Finance"""
        try:
            # Yahoo Finance search API
            search_url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                quotes = data.get('quotes', [])
                
                if quotes:
                    first_result = quotes[0]
                    # Obter logo através do modulo de dados
                    if 'longname' in first_result:
                        # Construir URL baseada no nome da empresa
                        company_name = first_result['longname']
                        logo_url = self._get_clearbit_logo(company_name)
                        
                        if logo_url:
                            logger.debug(f"Logo obtido via Yahoo/Clearbit para {ticker}: {logo_url}")
                            return logo_url
        
        except Exception as e:
            logger.debug(f"Erro ao obter logo do Yahoo para {ticker}: {e}")
        
        return None
    
    def _get_clearbit_logo(self, company_name: str) -> Optional[str]:
        """Obtém logo via Clearbit API"""
        try:
            # Clearbit Logo API (gratuita para uso moderado)
            url = f"https://logo.clearbit.com/v1/brands/domain"
            params = {
                'name': company_name.replace(' S.A.', '').replace(' ', '').lower(),
                'size': 'large',
                'format': 'png'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                svg_url = data.get('svg_uri')
                if svg_url:
                    # Converter SVG para URL de imagem se necessário
                    png_url = svg_url.replace('.svg', '.png')
                    return png_url
        
        except Exception as e:
            logger.debug(f"Erro ao obter logo do Clearbit para {company_name}: {e}")
        
        return None
    
    def _get_logo_alternative(self, ticker: str) -> Optional[str]:
        """Obtém logo de fontes alternativas"""
        try:
            # Tentar Google Logo API (simples)
            # Usando uma abordagem genérica baseada no ticker
            
            # Para empresas brasileiras conhecidas
            known_logos = {
                'PETR3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Petrobras_logo.svg/200px-Petrobras_logo.svg.png',
                'PETR4': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Petrobras_logo.svg/200px-Petrobras_logo.svg.png',
                'VALE3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Vale_logo.svg/200px-Vale_logo.svg.png',
                'ITUB4': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Ita%C3%BA_Unibanco_logo.svg/200px-Ita%C3%BA_Unibanco_logo.svg.png',
                'BBDC4': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Banco_Bradesco_logo.svg/200px-Banco_Bradesco_logo.svg.png',
                'BBAS3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Banco_do_Brasil_logo.svg/200px-Banco_do_Brasil_logo.svg.png',
                'WEGE3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Weg_logo.svg/200px-Weg_logo.svg.png',
                'MGLU3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Magazine_Luiza_logo.svg/200px-Magazine_Luiza_logo.svg.png',
                'GGBR4': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Gerdau_logo.svg/200px-Gerdau_logo.svg.png',
                'ABEV3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Ambev_logo.svg/200px-Ambev_logo.svg.png',
                'B3SA3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/B3.svg/200px-B3.svg.png',
                'SUZB3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Suzano_logo.svg/200px-Suzano_logo.svg.png'
            }
            
            # Tentar匹配 exato
            if ticker in known_logos:
                logo_url = known_logos[ticker]
                logger.debug(f"Logo obtido de repositório conhecido para {ticker}: {logo_url}")
                return logo_url
            
            # Fallback genérico baseado no ticker
            if ticker.endswith(('3', '4', '5', '6')):
                # Gerar logo placeholder genérico
                return f"https://ui-avatars.com/api/?name={ticker}&background=random&rounded=true"
            
        except Exception as e:
            logger.debug(f"Erro ao obter logo alternativo para {ticker}: {e}")
        
        return None
    
    def _save_logo_cache(self, ticker: str, logo_url: str):
        """Salva URL do logo em cache"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{ticker}.txt")
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(logo_url)
            logger.debug(f"Logo cacheado para {ticker}: {logo_url}")
        except Exception as e:
            logger.warning(f"Erro ao salvar cache do logo para {ticker}: {e}")
    
    def update_logos_for_all_stocks(self, limit: int = None) -> Dict[str, int]:
        """
        Atualiza logos para todas as ações que não têm
        
        Args:
            limit: Limite de ações a processar
            
        Returns:
            Dict: Estatísticas da atualização
        """
        stats = {
            'total_processed': 0,
            'logos_updated': 0,
            'logos_not_found': 0,
            'errors': 0
        }
        
        # Buscar ações que não têm logo_url
        query = self.db.query(Stock).filter(
            (Stock.logo_url.is_(None)) | 
            (Stock.logo_url == '')
        )
        
        if limit:
            query = query.limit(limit)
        
        stocks = query.all()
        logger.info(f"Processando {len(stocks)} ações para atualização de logos")
        
        for stock in stocks:
            try:
                stats['total_processed'] += 1
                
                logo_url = self.get_logo_url(stock.ticker, force_refresh=True)
                
                if logo_url:
                    stock.logo_url = logo_url
                    stats['logos_updated'] += 1
                    logger.debug(f"Logo atualizado para {stock.ticker}: {logo_url}")
                else:
                    stats['logos_not_found'] += 1
                    logger.debug(f"Logo não encontrado para {stock.ticker}")
                
                # Salvar a cada 10 atualizações
                if stats['total_processed'] % 10 == 0:
                    self.db.commit()
                    
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Erro ao processar logo para {stock.ticker}: {e}")
        
        # Commit final
        self.db.commit()
        
        logger.info(f"Atualização de logos concluída: {stats}")
        return stats
    
    def get_logo_statistics(self) -> Dict:
        """Retorna estatísticas sobre a cobertura de logos no banco"""
        total = self.db.query(Stock).count()
        with_logo = self.db.query(Stock).filter(
            (Stock.logo_url.isnot(None)) & (Stock.logo_url != '')
        ).count()
        without_logo = total - with_logo
        
        return {
            'total_stocks': total,
            'with_logo': with_logo,
            'without_logo': without_logo,
            'coverage_percentage': (with_logo / total * 100) if total > 0 else 0,
            'cache_size': len(os.listdir(self.cache_dir)) if os.path.exists(self.cache_dir) else 0
        }
    
    def clear_logo_cache(self):
        """Limpa todo o cache de logos"""
        try:
            if os.path.exists(self.cache_dir):
                import shutil
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
                logger.info("Cache de logos limpo com sucesso")
            else:
                logger.info("Diretório de cache não existe")
        except Exception as e:
            logger.error(f"Erro ao limpar cache de logos: {e}")
    
    def validate_logo_url(self, url: str) -> bool:
        """Valida se uma URL de logo é válida"""
        if not url or not isinstance(url, str):
            return False
        
        # Verificar se é uma URL válida
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Verificar se é uma imagem (extensões comuns)
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']
        return any(url.lower().endswith(ext) for ext in image_extensions)