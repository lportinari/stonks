import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'stonks-secret-key-2024'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///database/stocks.db'
    
    # API Keys
    BRAPI_API_KEY = os.environ.get('BRAPI_API_KEY')
    ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')
    
    # Pesos padrão dos indicadores (soma deve ser 1.0)
    DEFAULT_WEIGHTS = {
        'dy': 0.25,      # Dividend Yield
        'pl': 0.20,      # P/L
        'pvp': 0.20,     # P/VP
        'roe': 0.20,     # ROE
        'margem_liquida': 0.15  # Margem Líquida
    }
    
    # Configurações de scraping
    FUNDAMENTUS_URL = 'https://www.fundamentus.com.br/resultado.php'
    
    # Limites para indicadores (para normalização)
    INDICATOR_LIMITS = {
        'dy': {'min': 0, 'max': 0.20},          # 0% a 20%
        'pl': {'min': 0, 'max': 50},            # 0 a 50
        'pvp': {'min': 0, 'max': 10},           # 0 a 10
        'roe': {'min': 0, 'max': 0.50},         # 0% a 50%
        'margem_liquida': {'min': -0.20, 'max': 0.30}  # -20% a 30%
    }
    
    # Cache settings
    CACHE_DURATION_HOURS = 24
    
    # Pagination
    STOCKS_PER_PAGE = 50