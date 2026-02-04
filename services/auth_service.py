import logging
from typing import Dict, Any, Optional
from services.modulo_auth_client import auth_client
from services.jwt_validator import jwt_validator

logger = logging.getLogger(__name__)

class AuthService:
    """Serviço responsável pela autenticação via modulo-auth"""
    
    def login(self, email: str, password: str, ip: str = None) -> Dict[str, Any]:
        """
        Realiza login através do modulo-auth
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            ip: IP do usuário (para logs)
            
        Returns:
            Dict com tokens e dados do usuário
        """
        try:
            result = auth_client.login(email, password)
            
            if result.get('success') and result.get('access_token'):
                # Sucesso - retornar dados do módulo-auth
                return {
                    'success': True,
                    'message': 'Login realizado com sucesso!',
                    'access_token': result.get('access_token'),
                    'refresh_token': result.get('refresh_token'),
                    'user': result.get('user', {})
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', 'Erro ao fazer login')
                }
                
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return {
                'success': False,
                'message': f'Erro no login: {str(e)}'
            }
    
    def register(self, email: str, password: str, first_name: str, last_name: str) -> Dict[str, Any]:
        """
        Cria um novo usuário através do modulo-auth
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            first_name: Primeiro nome
            last_name: Sobrenome
            
        Returns:
            Dict com dados do usuário criado
        """
        try:
            # Validar requisitos de senha (modulo-auth exige mínimo 12 caracteres)
            if len(password) < 12:
                return {
                    'success': False,
                    'message': 'A senha deve ter pelo menos 12 caracteres'
                }
            
            result = auth_client.register(email, password, first_name, last_name)
            
            if result.get('success'):
                return {
                    'success': True,
                    'message': 'Usuário criado com sucesso! Faça login para continuar.',
                    'user': result.get('user', {})
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', 'Erro ao criar usuário')
                }
                
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            return {
                'success': False,
                'message': f'Erro ao criar usuário: {str(e)}'
            }
    
    def logout(self, access_token: str) -> Dict[str, Any]:
        """
        Faz logout através do modulo-auth
        
        Args:
            access_token: Access token atual
            
        Returns:
            Dict com resultado
        """
        try:
            auth_client.logout(access_token)
            return {
                'success': True,
                'message': 'Logout realizado com sucesso!'
            }
        except Exception as e:
            logger.error(f"Erro no logout: {e}")
            return {
                'success': True,  # Logout sempre considerado sucesso (mesmo se falhar)
                'message': 'Logout realizado com sucesso!'
            }
    
    def logout_all(self, access_token: str) -> Dict[str, Any]:
        """
        Faz logout de todos os dispositivos através do modulo-auth
        
        Args:
            access_token: Access token atual
            
        Returns:
            Dict com resultado
        """
        try:
            auth_client.logout_all(access_token)
            return {
                'success': True,
                'message': 'Logout de todos os dispositivos realizado com sucesso!'
            }
        except Exception as e:
            logger.error(f"Erro no logout-all: {e}")
            return {
                'success': True,
                'message': 'Logout de todos os dispositivos realizado com sucesso!'
            }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Renova o access token através do modulo-auth
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            Dict com novo access token
        """
        try:
            result = auth_client.refresh_token(refresh_token)
            
            if result.get('success'):
                return {
                    'success': True,
                    'message': 'Token renovado com sucesso!',
                    'access_token': result.get('access_token'),
                    'refresh_token': result.get('refresh_token', refresh_token)
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', 'Erro ao renovar token')
                }
                
        except Exception as e:
            logger.error(f"Erro ao renovar token: {e}")
            return {
                'success': False,
                'message': f'Erro ao renovar token: {str(e)}'
            }
    
    def get_user(self, user_id: str, access_token: str) -> Dict[str, Any]:
        """
        Busca dados de um usuário através do modulo-auth
        
        Args:
            user_id: UUID do usuário
            access_token: Access token válido
            
        Returns:
            Dict com dados do usuário
        """
        try:
            result = auth_client.get_user(user_id, access_token)
            
            if result.get('success'):
                return {
                    'success': True,
                    'user': result.get('user', {})
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', 'Erro ao buscar usuário')
                }
                
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return {
                'success': False,
                'message': f'Erro ao buscar usuário: {str(e)}'
            }
    
    def update_user(self, user_id: str, access_token: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza dados de um usuário através do modulo-auth
        
        Args:
            user_id: UUID do usuário
            access_token: Access token válido
            data: Dados a atualizar (ex: {'firstName': 'Novo Nome'})
            
        Returns:
            Dict com dados atualizados do usuário
        """
        try:
            result = auth_client.update_user(user_id, access_token, data)
            
            if result.get('success'):
                return {
                    'success': True,
                    'message': 'Dados atualizados com sucesso!',
                    'user': result.get('user', {})
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', 'Erro ao atualizar usuário')
                }
                
        except Exception as e:
            logger.error(f"Erro ao atualizar usuário: {e}")
            return {
                'success': False,
                'message': f'Erro ao atualizar usuário: {str(e)}'
            }
    
    def validate_token(self, token: str) -> bool:
        """
        Valida um token JWT localmente
        
        Args:
            token: Token JWT string
            
        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            return jwt_validator.validate_token(token)
        except Exception as e:
            logger.error(f"Erro ao validar token: {e}")
            return False
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extrai o ID do usuário de um token JWT
        
        Args:
            token: Token JWT string
            
        Returns:
            UUID do usuário ou None
        """
        try:
            return jwt_validator.get_user_id(token)
        except Exception as e:
            logger.error(f"Erro ao extrair user_id do token: {e}")
            return None
    
    def get_user_data_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Extrai dados do usuário de um token JWT
        
        Args:
            token: Token JWT string
            
        Returns:
            Dict com dados do usuário ou None
        """
        try:
            return jwt_validator.get_user_data(token)
        except Exception as e:
            logger.error(f"Erro ao extrair dados do token: {e}")
            return None
    
    def check_email_available(self, email: str) -> bool:
        """
        Verifica se um email está disponível (não implementado no modulo-auth)
        
        Args:
            email: Email a verificar
            
        Returns:
            bool: True se disponível, False caso contrário
        """
        # O modulo-auth não tem endpoint para verificar email
        # Esta verificação será feita na tentativa de registro
        return True


# Instância global do serviço
auth_service = AuthService()