import sqlite3
import bcrypt
import secrets
import datetime
from flask_login import UserMixin

class User(UserMixin):
    """Modelo de Usuário para SQLite"""
    
    def __init__(self, id, nome, email, senha_hash, email_verificado=False, 
                 token_verificacao=None, token_reset_senha=None, token_expiracao=None,
                 data_cadastro=None, ultimo_login=None, ativo=True):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha_hash = senha_hash
        self.email_verificado = email_verificado
        self.token_verificacao = token_verificacao
        self.token_reset_senha = token_reset_senha
        self.token_expiracao = token_expiracao
        self.data_cadastro = data_cadastro
        self.ultimo_login = ultimo_login
        self.ativo = ativo
    
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
    
    def set_senha(self, senha):
        """Define o hash da senha"""
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verificar_senha(self, senha):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))
    
    def gerar_reset_token(self):
        """Gera um token para reset de senha"""
        self.token_reset_senha = secrets.token_urlsafe(32)
        self.token_expiracao = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        return self.token_reset_senha
    
    def verificar_reset_token(self, token):
        """Verifica se o token de reset é válido"""
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
    
    def gerar_verification_token(self):
        """Gera um token para verificação de email"""
        self.token_verificacao = secrets.token_urlsafe(32)
        # Não expira token de verificação para simplificar
        return self.token_verificacao
    
    def verificar_verification_token(self, token):
        """Verifica se o token de verificação é válido"""
        return self.token_verificacao == token
    
    def verificar_email(self):
        """Marca o email como verificado"""
        self.email_verificado = True
        self.token_verificacao = None
    
    def atualizar_ultimo_login(self, ip=None):
        """Atualiza data do último login"""
        self.ultimo_login = datetime.datetime.now(datetime.timezone.utc)
    
    def to_dict(self):
        """Converte o objeto para dicionário (sem dados sensíveis)"""
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'email_verificado': self.email_verificado,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro and hasattr(self.data_cadastro, 'isoformat') else self.data_cadastro,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login and hasattr(self.ultimo_login, 'isoformat') else self.ultimo_login
        }
    
    def __repr__(self):
        return f'<User {self.nome} - {self.email}>'

# Funções para trabalhar com o banco de dados
def get_user_by_email(email):
    """Busca usuário por email"""
    with sqlite3.connect('database/stocks.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        
        if row:
            return User(
                id=row['id'],
                nome=row['nome'],
                email=row['email'],
                senha_hash=row['senha_hash'],
                email_verificado=bool(row['email_verificado']),
                token_verificacao=row['token_verificacao'],
                token_reset_senha=row['token_reset_senha'],
                token_expiracao=row['token_expiracao'],
                data_cadastro=row['data_cadastro'],
                ultimo_login=row['ultimo_login'],
                ativo=bool(row['ativo'])
            )
        return None

def get_user_by_id(user_id):
    """Busca usuário por ID"""
    with sqlite3.connect('database/stocks.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            return User(
                id=row['id'],
                nome=row['nome'],
                email=row['email'],
                senha_hash=row['senha_hash'],
                email_verificado=bool(row['email_verificado']),
                token_verificacao=row['token_verificacao'],
                token_reset_senha=row['token_reset_senha'],
                token_expiracao=row['token_expiracao'],
                data_cadastro=row['data_cadastro'],
                ultimo_login=row['ultimo_login'],
                ativo=bool(row['ativo'])
            )
        return None

def create_user(nome, email, senha):
    """Cria um novo usuário"""
    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    with sqlite3.connect('database/stocks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (nome, email, senha_hash, email_verificado, token_verificacao)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, email, senha_hash, False, None))
        conn.commit()
        return cursor.lastrowid

def update_user(user):
    """Atualiza dados do usuário"""
    with sqlite3.connect('database/stocks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET 
                nome = ?, email_verificado = ?, token_verificacao = ?, 
                token_reset_senha = ?, token_expiracao = ?, 
                ultimo_login = ?, ativo = ?
            WHERE id = ?
        ''', (
            user.nome, user.email_verificado, user.token_verificacao,
            user.token_reset_senha, user.token_expiracao, 
            user.ultimo_login, user.ativo, user.id
        ))
        conn.commit()

def user_exists(email):
    """Verifica se usuário já existe"""
    with sqlite3.connect('database/stocks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
        return cursor.fetchone()[0] > 0