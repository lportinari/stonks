from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from config import Config
import logging

logger = logging.getLogger(__name__)

# Configuração do banco de dados com suporte a PostgreSQL e SQLite
db_type = Config.get_db_type()

if db_type == 'postgresql':
    # Configurações para PostgreSQL com pool de conexões
    engine = create_engine(
        Config.DATABASE_URL,
        echo=False,
        poolclass=QueuePool,
        pool_size=10,              # Número de conexões permanentes
        max_overflow=20,            # Conexões extras permitidas além do pool
        pool_pre_ping=True,           # Verifica conexões antes de usar
        pool_recycle=3600            # Recicla conexões após 1 hora
    )
else:
    # SQLite (sem pool necessário)
    engine = create_engine(
        Config.DATABASE_URL,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Event listeners para otimizações específicas do SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configura pragmas do SQLite para melhor performance"""
    if db_type == 'sqlite':
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Banco de dados inicializado com sucesso: {Config.get_db_type()}")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise

def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Testa a conexão com o banco de dados"""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        logger.info(f"Conexão com {Config.get_db_type()} estabelecida com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados {Config.get_db_type()}: {e}")
        return False
