from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import bcrypt
import secrets
import datetime
from flask_login import UserMixin

class User(Base, UserMixin):
    """
    Modelo de Usuário usando SQLAlchemy ORM
    
    Suporta:
    - SQLite (atual)
    - PostgreSQL (futuro)
    - MySQL (futuro)
    """
    __tablename__ = 'users'
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    
    # Verificação de email
    email_verificado = Column(Boolean, default=False)
    token_verificacao = Column(String(100))
    
    # Reset de senha
    token_reset_senha = Column(String(100))
    token_expiracao = Column(DateTime(timezone=True))
    
    # Metadados
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_login = Column(DateTime(timezone=True))
    ativo = Column(Boolean, default=True)
    
    # Relacionamento com compras (se existir tabela purchases)
    # purchases = relationship("Purchase", back_populates="user")
    
    def __repr__(self):
        return f'<User {self.nome} - {self.email}>'
    
    # Métodos de Flask-Login
    @property
    def is_authenticated(self):
        """Flask-Login property"""
        return True
    
    @property
    def is_active(self):
        """Flask-Login property"""
        return self.ativo
    
    @property
    def is_anonymous(self):
        """Flask-Login property"""
        return False
    
    def get_id(self):
        """Flask-Login method"""
        return str(self.id)
    
    # Métodos de Senha
    def set_senha(self, senha):
        """
        Define o hash da senha usando bcrypt
        
        Args:
            senha (str): Senha em texto plano
        """
        if isinstance(senha, str):
            senha = senha.encode('utf-8')
        self.senha_hash = bcrypt.hashpw(senha, bcrypt.gensalt()).decode('utf-8')
    
    def verificar_senha(self, senha):
        """
        Verifica se a senha está correta
        
        Args:
            senha (str): Senha a verificar
            
        Returns:
            bool: True se senha correta, False caso contrário
        """
        if isinstance(senha, str):
            senha = senha.encode('utf-8')
        if isinstance(self.senha_hash, str):
            senha_hash = self.senha_hash.encode('utf-8')
        else:
            senha_hash = self.senha_hash
        return bcrypt.checkpw(senha, senha_hash)
    
    # Métodos de Tokens de Reset de Senha
    def gerar_reset_token(self):
        """
        Gera um token para reset de senha válido por 2 horas
        
        Returns:
            str: Token gerado
        """
        self.token_reset_senha = secrets.token_urlsafe(32)
        self.token_expiracao = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        return self.token_reset_senha
    
    def verificar_reset_token(self, token):
        """
        Verifica se o token de reset é válido
        
        Args:
            token (str): Token a verificar
            
        Returns:
            bool: True se token válido, False caso contrário
        """
        if not self.token_reset_senha or not self.token_expiracao:
            return False
        
        if self.token_reset_senha != token:
            return False
        
        if datetime.datetime.now(datetime.timezone.utc) > self.token_expiracao:
            return False
        
        return True
    
    def limpar_reset_token(self):
        """Limpa o token de reset após uso"""
        self.token_reset_senha = None
        self.token_expiracao = None
    
    # Métodos de Verificação de Email
    def gerar_verification_token(self):
        """
        Gera um token para verificação de email
        
        Returns:
            str: Token gerado
        """
        self.token_verificacao = secrets.token_urlsafe(32)
        return self.token_verificacao
    
    def verificar_verification_token(self, token):
        """
        Verifica se o token de verificação é válido
        
        Args:
            token (str): Token a verificar
            
        Returns:
            bool: True se token válido, False caso contrário
        """
        return self.token_verificacao == token
    
    def verificar_email(self):
        """Marca o email como verificado"""
        self.email_verificado = True
        self.token_verificacao = None
    
    # Métodos Auxiliares
    def atualizar_ultimo_login(self, ip=None):
        """
        Atualiza data do último login
        
        Args:
            ip (str, opcional): IP do usuário
        """
        self.ultimo_login = datetime.datetime.now(datetime.timezone.utc)
    
    def to_dict(self):
        """
        Converte o objeto para dicionário (sem dados sensíveis)
        
        Returns:
            dict: Dicionário com dados do usuário
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'email_verificado': self.email_verificado,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None
        }


# Funções helper para compatibilidade (legado, mas será removido)
# TODO: Remover após refatorar todas as rotas para usar ORM
def get_user_by_email(email):
    """
    Busca usuário por email usando ORM
    
    Args:
        email (str): Email do usuário
        
    Returns:
        User: Objeto User ou None
    """
    from .database import SessionLocal
    with SessionLocal() as db:
        return db.query(User).filter(User.email == email).first()


def get_user_by_id(user_id):
    """
    Busca usuário por ID usando ORM
    
    Args:
        user_id (int): ID do usuário
        
    Returns:
        User: Objeto User ou None
    """
    from .database import SessionLocal
    with SessionLocal() as db:
        return db.query(User).filter(User.id == user_id).first()


def create_user(nome, email, senha):
    """
    Cria um novo usuário usando ORM
    
    Args:
        nome (str): Nome do usuário
        email (str): Email do usuário
        senha (str): Senha em texto plano
        
    Returns:
        int: ID do usuário criado
    """
    from .database import SessionLocal
    with SessionLocal() as db:
        user = User(
            nome=nome,
            email=email
        )
        user.set_senha(senha)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user.id


def update_user(user):
    """
    Atualiza dados do usuário no banco
    
    Args:
        user (User): Objeto User com dados atualizados
    """
    from .database import SessionLocal
    with SessionLocal() as db:
        db.merge(user)
        db.commit()


def user_exists(email):
    """
    Verifica se usuário já existe usando ORM
    
    Args:
        email (str): Email do usuário
        
    Returns:
        bool: True se usuário existe, False caso contrário
    """
    from .database import SessionLocal
    with SessionLocal() as db:
        return db.query(User).filter(User.email == email).first() is not None