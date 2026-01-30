import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from config import Config

logger = logging.getLogger(__name__)

class CacheManager:
    """Gerenciador de cache para dados das ações"""
    
    def __init__(self, cache_dir: str = "database/cache"):
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(hours=Config.CACHE_DURATION_HOURS)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Garante que o diretório de cache existe"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_file_path(self, key: str) -> str:
        """Retorna o path do arquivo de cache para uma chave"""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """Verifica se o cache ainda é válido"""
        if not os.path.exists(cache_file):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        return datetime.now() - file_time < self.cache_duration
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém dados do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Dados do cache ou None se inválido/inexistente
        """
        cache_file = self._get_cache_file_path(key)
        
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Cache hit para chave: {key}")
                return data
        except Exception as e:
            logger.error(f"Erro ao ler cache {key}: {e}")
            return None
    
    def set(self, key: str, data: Any) -> bool:
        """
        Salva dados no cache
        
        Args:
            key: Chave do cache
            data: Dados para salvar
            
        Returns:
            bool: True se salvo com sucesso
        """
        cache_file = self._get_cache_file_path(key)
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"Cache salvo para chave: {key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar cache {key}: {e}")
            return False
    
    def invalidate(self, key: str) -> bool:
        """
        Invalida uma entrada específica do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            bool: True se removido com sucesso
        """
        cache_file = self._get_cache_file_path(key)
        
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.debug(f"Cache invalidado: {key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao invalidar cache {key}: {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Limpa todo o cache
        
        Returns:
            bool: True se limpo com sucesso
        """
        try:
            if os.path.exists(self.cache_dir):
                for file in os.listdir(self.cache_dir):
                    if file.endswith('.json'):
                        os.remove(os.path.join(self.cache_dir, file))
                logger.info("Todo o cache foi limpo")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o cache atual
        
        Returns:
            Dict: Informações do cache
        """
        info = {
            'cache_dir': self.cache_dir,
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600,
            'total_files': 0,
            'total_size_mb': 0,
            'oldest_file': None,
            'newest_file': None,
            'expired_files': 0
        }
        
        if not os.path.exists(self.cache_dir):
            return info
        
        files = []
        total_size = 0
        
        for file in os.listdir(self.cache_dir):
            if file.endswith('.json'):
                file_path = os.path.join(self.cache_dir, file)
                file_size = os.path.getsize(file_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                files.append({
                    'name': file,
                    'path': file_path,
                    'size': file_size,
                    'time': file_time
                })
                
                total_size += file_size
        
        if files:
            files.sort(key=lambda x: x['time'])
            
            oldest = files[0]
            newest = files[-1]
            
            now = datetime.now()
            expired_count = sum(1 for f in files if now - f['time'] >= self.cache_duration)
            
            info.update({
                'total_files': len(files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_file': {
                    'name': oldest['name'],
                    'age_hours': (now - oldest['time']).total_seconds() / 3600
                },
                'newest_file': {
                    'name': newest['name'],
                    'age_hours': (now - newest['time']).total_seconds() / 3600
                },
                'expired_files': expired_count
            })
        
        return info
    
    def cleanup_expired(self) -> int:
        """
        Remove arquivos de cache expirados
        
        Returns:
            int: Número de arquivos removidos
        """
        if not os.path.exists(self.cache_dir):
            return 0
        
        removed_count = 0
        now = datetime.now()
        
        for file in os.listdir(self.cache_dir):
            if file.endswith('.json'):
                file_path = os.path.join(self.cache_dir, file)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if now - file_time >= self.cache_duration:
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        logger.debug(f"Arquivo expirado removido: {file}")
                    except Exception as e:
                        logger.error(f"Erro ao remover arquivo expirado {file}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleanup: {removed_count} arquivos expirados removidos")
        
        return removed_count


# Cache keys específicos para a aplicação
class CacheKeys:
    STOCKS_DATA = "stocks_data"
    RANKING_DATA = "ranking_data"
    SECTOR_STATS = "sector_stats"
    TOP_STOCKS = "top_stocks"
    STOCK_DETAIL = "stock_detail"  # Usado com suffixo: stock_detail_{ticker}


# Função decoradora para cache (opcional)
def cached_result(key_func, duration_hours: Optional[int] = None):
    """
    Decorador para cachear resultados de funções
    
    Args:
        key_func: Função que gera a chave do cache baseado nos argumentos
        duration_hours: Duração customizada do cache em horas
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_manager = CacheManager()
            
            # Gerar chave do cache
            cache_key = key_func(*args, **kwargs)
            
            # Tentar obter do cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator