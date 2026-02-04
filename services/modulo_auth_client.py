import requests
import logging
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class ModuloAuthClient:
    """Cliente HTTP para comunicação com o serviço modulo-auth"""
    
    def __init__(self):
        self.base_url = Config.MODULO_AUTH_URL.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Faz uma requisição HTTP para o modulo-auth
        
        Args:
            method: Método HTTP (GET, POST, PATCH, DELETE)
            endpoint: Endpoint da API (ex: /auth/login)
            data: Dados a serem enviados no corpo da requisição
            headers: Headers adicionais
            
        Returns:
            Dict com a resposta da API
            
        Raises:
            requests.RequestException: Erro na requisição HTTP
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                headers=headers
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            try:
                error_data = e.response.json()
                return {
                    'success': False,
                    'message': error_data.get('message', 'Erro desconhecido'),
                    'statusCode': e.response.status_code
                }
            except:
                return {
                    'success': False,
                    'message': str(e),
                    'statusCode': e.response.status_code
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            return {
                'success': False,
                'message': f'Erro de conexão com modulo-auth: {str(e)}'
            }
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Realiza login no modulo-auth
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            Dict com tokens e dados do usuário
        """
        data = {
            'email': email,
            'password': password
        }
        
        result = self._make_request('POST', '/auth/login', data=data)
        
        if result.get('success'):
            # Adicionar flag de sucesso para consistência
            result['success'] = True
        
        return result
    
    def register(self, email: str, password: str, first_name: str, last_name: str) -> Dict[str, Any]:
        """
        Cria um novo usuário no modulo-auth
        
        Args:
            email: Email do usuário
            password: Senha do usuário (mínimo 12 caracteres)
            first_name: Primeiro nome
            last_name: Sobrenome
            
        Returns:
            Dict com dados do usuário criado
        """
        data = {
            'email': email,
            'password': password,
            'firstName': first_name,
            'lastName': last_name
        }
        
        result = self._make_request('POST', '/users', data=data)
        
        # A API retorna statusCode 201 com os dados do usuário
        if result.get('statusCode') == 201 or result.get('data'):
            return {
                'success': True,
                'message': 'Usuário criado com sucesso',
                'user': result.get('data', {})
            }
        
        return {
            'success': False,
            'message': result.get('message', 'Erro ao criar usuário')
        }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Renova o access token usando o refresh token
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            Dict com novo access token
        """
        data = {
            'refresh_token': refresh_token
        }
        
        result = self._make_request('POST', '/auth/refresh', data=data)
        
        if result.get('data'):
            return {
                'success': True,
                'access_token': result['data'].get('access_token'),
                'refresh_token': result['data'].get('refresh_token', refresh_token)
            }
        
        return {
            'success': False,
            'message': result.get('message', 'Erro ao renovar token')
        }
    
    def logout(self, access_token: str) -> Dict[str, Any]:
        """
        Faz logout do dispositivo atual
        
        Args:
            access_token: Access token atual
            
        Returns:
            Dict com resultado
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        result = self._make_request('POST', '/auth/logout', headers=headers)
        
        return {
            'success': True,
            'message': 'Logout realizado com sucesso'
        }
    
    def logout_all(self, access_token: str) -> Dict[str, Any]:
        """
        Faz logout de todos os dispositivos
        
        Args:
            access_token: Access token atual
            
        Returns:
            Dict com resultado
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        result = self._make_request('POST', '/auth/logout-all', headers=headers)
        
        return {
            'success': True,
            'message': 'Logout de todos os dispositivos realizado com sucesso'
        }
    
    def get_user(self, user_id: str, access_token: str) -> Dict[str, Any]:
        """
        Busca dados de um usuário
        
        Args:
            user_id: UUID do usuário
            access_token: Access token válido
            
        Returns:
            Dict com dados do usuário
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        result = self._make_request('GET', f'/users/{user_id}', headers=headers)
        
        if result.get('data'):
            return {
                'success': True,
                'user': result['data']
            }
        
        return {
            'success': False,
            'message': result.get('message', 'Erro ao buscar usuário')
        }
    
    def update_user(self, user_id: str, access_token: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza dados de um usuário
        
        Args:
            user_id: UUID do usuário
            access_token: Access token válido
            data: Dados a atualizar (ex: {'firstName': 'Novo Nome'})
            
        Returns:
            Dict com dados atualizados do usuário
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        result = self._make_request('PATCH', f'/users/{user_id}', data=data, headers=headers)
        
        if result.get('data'):
            return {
                'success': True,
                'message': 'Usuário atualizado com sucesso',
                'user': result['data']
            }
        
        return {
            'success': False,
            'message': result.get('message', 'Erro ao atualizar usuário')
        }
    
    def health_check(self) -> bool:
        """
        Verifica se o modulo-auth está disponível
        
        Returns:
            bool: True se disponível, False caso contrário
        """
        try:
            result = self._make_request('GET', '/health')
            return 'status' in result or result.get('status') == 'ok'
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False


# Instância global do cliente
auth_client = ModuloAuthClient()