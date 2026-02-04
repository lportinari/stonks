import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'stonks-secret-key-2024'
    
    # Configuração do banco de dados
    # Prioridade: Variável de ambiente > PostgreSQL padrão > SQLite fallback
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        # Tentar conectar ao PostgreSQL
        try:
            import psycopg2
            pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
            pg_port = int(os.environ.get('POSTGRES_PORT', '5432'))
            pg_db = os.environ.get('POSTGRES_DB', 'stonks')
            pg_user = os.environ.get('POSTGRES_USER', 'postgres')
            pg_password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
            
            # Testar conexão PostgreSQL
            conn = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                database=pg_db,
                user=pg_user,
                password=pg_password,
                connect_timeout=3
            )
            conn.close()
            
            DATABASE_URL = f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}'
            print(f"INFO: Usando PostgreSQL em {pg_host}:{pg_port}")
        except ImportError:
            print("INFO: psycopg2 não instalado, usando SQLite")
            DATABASE_URL = 'sqlite:///database/stocks.db'
        except Exception as e:
            print(f"INFO: PostgreSQL não disponível ({str(e)}), usando SQLite")
            DATABASE_URL = 'sqlite:///database/stocks.db'
    
    @staticmethod
    def get_db_type():
        """Retorna o tipo de banco de dados sendo usado"""
        url = Config.DATABASE_URL.lower() if Config.DATABASE_URL else ''
        if 'postgresql' in url:
            return 'postgresql'
        elif 'mysql' in url:
            return 'mysql'
        else:
            return 'sqlite'
    
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
    
    # Modulo-Auth Configuration
    MODULO_AUTH_URL = os.environ.get('MODULO_AUTH_URL', 'http://backend:3000/api')
    MODULO_AUTH_JWT_SECRET = os.environ.get('MODULO_AUTH_JWT_SECRET', 'your-jwt-secret-here')
