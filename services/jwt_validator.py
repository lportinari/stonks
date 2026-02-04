import jwt
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from config import Config
from functools import wraps

logger = logging.getLogger(__name__)

class JWTValidator:
    """Validador de tokens JWT do modulo-auth"""
    
    def __init__(self):
        self.secret = Config.MODULO_AUTH_JWT_SECRET
        self.algorithm = 'HS256'
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodifica e valida um token JWT
        
        Args:
            token: Token JWT string
            
        Returns:
            Dict com o payload do token ou None se inválido
        """
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
            
            # Verificar expiração
            if 'exp' in payload:
                exp = datetime.fromtimestamp(payload['exp'])
                if datetime.utcnow() > exp:
                    logger.warning("Token expirado")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erro ao decodificar token: {str(e)}")
            return None
    
    def validate_token(self, token: str) -> bool:
        """
        Valida se um token JWT é válido
        
        Args:
            token: Token JWT string
            
        Returns:
            bool: True se válido, False caso contrário
        """
        return self.decode_token(token) is not None
    
    def get_user_id(self, token: str) -> Optional[str]:
        """
        Extrai o ID do usuário do token JWT
        
        Args:
            token: Token JWT string
            
        Returns:
            UUID do usuário ou None se inválido
        """
        payload = self.decode_token(token)
        if payload and 'sub' in payload:
            return payload['sub']
        return None
    
    def get_user_data(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Extrai dados do usuário do token JWT
        
        Args:
            token: Token JWT string
            
        Returns:
            Dict com dados do usuário ou None se inválido
        """
        payload = self.decode_token(token)
        if not payload:
            return None
        
        return {
            'id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role'),
            'exp': payload.get('exp'),
            'iat': payload.get('iat')
        }


# Instância global do validador
jwt_validator = JWTValidator()


def get_token_from_request(request):
    """
    Extrai o token JWT da requisição
    
    Args:
        request: Objeto request do Flask
        
    Returns:
        Token JWT string ou None
    """
    # Tentar header Authorization
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]
    
    # Tentar query parameter
    token = request.args.get('token')
    if token:
        return token
    
    # Tentar cookie (opcional)
    token = request.cookies.get('access_token')
    if token:
        return token
    
    return None


def jwt_required(f):
    """
    Decorator para proteger rotas que exigem autenticação JWT
    
    Uso:
        @jwt_required
        def minha_rota():
            auth_id = request.jwt_user_id
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        token = get_token_from_request(request)
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token não fornecido'
            }), 401
        
        user_id = jwt_validator.get_user_id(token)
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'Token inválido ou expirado'
            }), 401
        
        # Adicionar user_id ao request object
        request.jwt_user_id = user_id
        request.jwt_token = token
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user_id():
    """
    Helper para obter o ID do usuário autenticado no contexto atual
    
    Returns:
        UUID do usuário ou None
    """
    from flask import request, g
    return getattr(request, 'jwt_user_id', None)


def get_current_token():
    """
    Helper para obter o token JWT do contexto atual
    
    Returns:
        Token JWT string ou None
    """
    from flask import request
    return getattr(request, 'jwt_token', None)