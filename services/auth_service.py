import smtplib
import logging
import bcrypt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models.user import User, get_user_by_email, get_user_by_id, create_user, update_user, user_exists
from flask import current_app
import os

logger = logging.getLogger(__name__)

class AuthService:
    """Serviço responsável pela autenticação e gestão de usuários"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
    
    def criar_usuario(self, nome: str, email: str, senha: str) -> Dict[str, Any]:
        """Cria um novo usuário"""
        try:
            # Verificar se email já existe
            if user_exists(email):
                return {'success': False, 'message': 'Email já cadastrado'}
            
            # Criar hash da senha primeiro
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Salvar no banco
            user_id = create_user(nome, email, senha_hash)
            
            # Criar objeto usuário com ID
            usuario = User(
                id=user_id,
                nome=nome, 
                email=email, 
                senha_hash=senha_hash,
                email_verificado=False
            )
            
            # Enviar email de verificação
            if self.smtp_user and self.smtp_password:
                self._enviar_email_verificacao(usuario)
            else:
                logger.warning("Configurações de email não encontradas. Pulando envio de verificação.")
                # Auto-verificar em ambiente de desenvolvimento
                if os.getenv('FLASK_ENV') == 'development':
                    usuario.verificar_email()
                    update_user(usuario)
            
            return {
                'success': True,
                'message': 'Usuário criado com sucesso! Verifique seu email para ativar a conta.',
                'user': usuario.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            return {'success': False, 'message': f'Erro ao criar usuário: {str(e)}'}
    
    def autenticar_usuario(self, email: str, senha: str, ip: str = None) -> Dict[str, Any]:
        """Autentica um usuário"""
        try:
            usuario = get_user_by_email(email)
            
            if not usuario:
                return {'success': False, 'message': 'Email ou senha incorretos'}
            
            if not usuario.ativo:
                return {'success': False, 'message': 'Conta desativada'}
            
            if not usuario.verificar_senha(senha):
                return {'success': False, 'message': 'Email ou senha incorretos'}
            
            # Atualizar último login
            usuario.atualizar_ultimo_login(ip)
            update_user(usuario)
            
            return {
                'success': True,
                'message': 'Login realizado com sucesso!',
                'user': usuario.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return {'success': False, 'message': f'Erro na autenticação: {str(e)}'}
    
    def solicitar_reset_senha(self, email: str) -> Dict[str, Any]:
        """Solicita reset de senha"""
        try:
            usuario = get_user_by_email(email)
            
            if not usuario:
                return {'success': False, 'message': 'Email não encontrado'}
            
            # Gerar token de reset
            token = usuario.gerar_reset_token()
            update_user(usuario)
            
            # Enviar email de reset
            if self.smtp_user and self.smtp_password:
                self._enviar_email_reset_senha(usuario, token)
            else:
                logger.warning("Configurações de email não encontradas. Pulando envio de email de reset.")
            
            return {
                'success': True,
                'message': 'Email de reset de senha enviado! Verifique sua caixa de entrada.'
            }
            
        except Exception as e:
            logger.error(f"Erro ao solicitar reset de senha: {e}")
            return {'success': False, 'message': f'Erro ao solicitar reset: {str(e)}'}
    
    def resetar_senha(self, token: str, nova_senha: str) -> Dict[str, Any]:
        """Reseta a senha usando o token"""
        try:
            from models.database import SessionLocal
            
            # Buscar usuário pelo token e fazer todas as operações no mesmo contexto
            with SessionLocal() as db:
                usuario = db.query(User).filter(User.token_reset_senha == token).first()
                
                if not usuario:
                    return {'success': False, 'message': 'Token inválido'}
            
                if not usuario.verificar_reset_token(token):
                    return {'success': False, 'message': 'Token expirado ou inválido'}
                
                # Resetar senha
                usuario.set_senha(nova_senha)
                usuario.limpar_reset_token()
                db.commit()
            
                return {
                    'success': True,
                    'message': 'Senha alterada com sucesso!'
                }
            
        except Exception as e:
            logger.error(f"Erro ao resetar senha: {e}")
            return {'success': False, 'message': f'Erro ao resetar senha: {str(e)}'}
    
    def verificar_email_token(self, token: str) -> Dict[str, Any]:
        """Verifica o email usando o token"""
        try:
            from models.database import SessionLocal
            
            # Buscar usuário pelo token e fazer todas as operações no mesmo contexto
            with SessionLocal() as db:
                usuario = db.query(User).filter(User.token_verificacao == token).first()
                
                if not usuario:
                    return {'success': False, 'message': 'Token inválido'}
                
                if not usuario.verificar_verification_token(token):
                    return {'success': False, 'message': 'Token expirado'}
                
                # Verificar email
                usuario.verificar_email()
                db.commit()
            
                return {
                    'success': True,
                    'message': 'Email verificado com sucesso!'
                }
            
        except Exception as e:
            logger.error(f"Erro na verificação de email: {e}")
            return {'success': False, 'message': f'Erro na verificação: {str(e)}'}
    
    def get_usuario_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuário por ID"""
        try:
            return get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return None
    
    def atualizar_usuario(self, user_id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza dados do usuário"""
        try:
            usuario = get_user_by_id(user_id)
            if not usuario:
                return {'success': False, 'message': 'Usuário não encontrado'}
            
            # Atualizar campos permitidos
            campos_permitidos = ['nome']
            for campo, valor in dados.items():
                if campo in campos_permitidos and hasattr(usuario, campo):
                    setattr(usuario, campo, valor)
            
            update_user(usuario)
            
            return {
                'success': True,
                'message': 'Dados atualizados com sucesso!',
                'user': usuario.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Erro ao atualizar usuário: {e}")
            return {'success': False, 'message': f'Erro ao atualizar: {str(e)}'}
    
    def alterar_senha(self, user_id: int, senha_atual: str, nova_senha: str) -> Dict[str, Any]:
        """Altera a senha do usuário"""
        try:
            usuario = get_user_by_id(user_id)
            if not usuario:
                return {'success': False, 'message': 'Usuário não encontrado'}
            
            if not usuario.verificar_senha(senha_atual):
                return {'success': False, 'message': 'Senha atual incorreta'}
            
            usuario.set_senha(nova_senha)
            update_user(usuario)
            
            return {
                'success': True,
                'message': 'Senha alterada com sucesso!'
            }
            
        except Exception as e:
            logger.error(f"Erro ao alterar senha: {e}")
            return {'success': False, 'message': f'Erro ao alterar senha: {str(e)}'}
    
    def _enviar_email_verificacao(self, usuario: User):
        """Envia email de verificação"""
        try:
            assunto = "Verifique seu email - Stonks"
            corpo = f"""
            <html>
            <body>
                <h2>Bem-vindo ao Stonks, {usuario.nome}!</h2>
                <p>Por favor, clique no link abaixo para verificar seu email e ativar sua conta:</p>
                <p><a href="{os.getenv('BASE_URL', 'http://localhost:5000')}/auth/verify-email/{usuario.token_verificacao}">
                    Verificar Email
                </a></p>
                <p>Se você não se cadastrou no Stonks, ignore este email.</p>
                <p>Este link expira em 24 horas.</p>
                <br>
                <p>Atenciosamente,<br>Equipe Stonks</p>
            </body>
            </html>
            """
            
            self._enviar_email(usuario.email, assunto, corpo)
            logger.info(f"Email de verificação enviado para {usuario.email}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de verificação: {e}")
    
    def _enviar_email_reset_senha(self, usuario: User, token: str):
        """Envia email de reset de senha"""
        try:
            assunto = "Reset de Senha - Stonks"
            corpo = f"""
            <html>
            <body>
                <h2>Reset de Senha</h2>
                <p>Olá {usuario.nome},</p>
                <p>Recebemos uma solicitação para resetar sua senha. Clique no link abaixo:</p>
                <p><a href="{os.getenv('BASE_URL', 'http://localhost:5000')}/auth/reset-password/{token}">
                    Resetar Senha
                </a></p>
                <p>Se você não solicitou esta alteração, ignore este email.</p>
                <p>Este link expira em 2 horas.</p>
                <br>
                <p>Atenciosamente,<br>Equipe Stonks</p>
            </body>
            </html>
            """
            
            self._enviar_email(usuario.email, assunto, corpo)
            logger.info(f"Email de reset enviado para {usuario.email}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de reset: {e}")
    
    def _enviar_email(self, para_email: str, assunto: str, corpo_html: str):
        """Envia email usando SMTP"""
        if not self.smtp_user or not self.smtp_password:
            raise Exception("Configurações de SMTP não encontradas")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From'] = self.from_email
        msg['To'] = para_email
        
        # Adicionar corpo HTML
        html_part = MIMEText(corpo_html, 'html')
        msg.attach(html_part)
        
        # Enviar email
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        server.send_message(msg)
        server.quit()