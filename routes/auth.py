from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from services.auth_service import auth_service
from services.jwt_validator import get_token_from_request, jwt_required, get_current_user_id
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    # Verificar se já está autenticado
    token = get_token_from_request(request)
    if token and auth_service.validate_token(token):
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        
        if not email or not senha:
            flash('Email e senha são obrigatórios', 'error')
            return render_template('auth/login.html')
        
        # Autenticar usuário via modulo-auth
        resultado = auth_service.login(email, senha, request.remote_addr)
        
        if resultado['success']:
            # Armazenar tokens na sessão
            session['access_token'] = resultado['access_token']
            session['refresh_token'] = resultado['refresh_token']
            session['user'] = resultado['user']
            
            # Também setar cookie para o frontend
            response = make_response(redirect(request.args.get('next') or url_for('main.index')))
            response.set_cookie('access_token', resultado['access_token'], httponly=True)
            response.set_cookie('refresh_token', resultado['refresh_token'], httponly=True)
            
            flash('Login realizado com sucesso!', 'success')
            return response
        else:
            flash(resultado['message'], 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de cadastro"""
    # Verificar se já está autenticado
    token = get_token_from_request(request)
    if token and auth_service.validate_token(token):
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        nome_completo = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        # Validações básicas
        if not nome_completo or not email or not senha:
            flash('Todos os campos são obrigatórios', 'error')
            return render_template('auth/register.html')
        
        # Separar nome e sobrenome
        partes_nome = nome_completo.split(' ', 1)
        first_name = partes_nome[0]
        last_name = partes_nome[1] if len(partes_nome) > 1 else ''
        
        if len(senha) < 12:
            flash('A senha deve ter pelo menos 12 caracteres', 'error')
            return render_template('auth/register.html')
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem', 'error')
            return render_template('auth/register.html')
        
        # Criar usuário via modulo-auth
        resultado = auth_service.register(email, senha, first_name, last_name)
        
        if resultado['success']:
            flash(resultado['message'], 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(resultado['message'], 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Logout do usuário"""
    # Remover tokens da sessão
    access_token = session.pop('access_token', None)
    refresh_token = session.pop('refresh_token', None)
    session.pop('user', None)
    
    # Fazer logout no modulo-auth
    if access_token:
        auth_service.logout(access_token)
    
    # Limpar cookies
    response = make_response(redirect(url_for('main.index')))
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    flash('Você saiu da sua conta.', 'info')
    return response

# Rotas de reset de senha e verificação de email não são mais necessárias
# pois são gerenciadas pelo modulo-auth
# Essas rotas podem ser removidas ou redirecionadas para documentação

@auth_bp.route('/profile')
@jwt_required
def profile():
    """Perfil do usuário"""
    user_id = request.jwt_user_id
    token = request.jwt_token
    
    # Buscar dados atualizados do usuario
    resultado = auth_service.get_user(user_id, token)
    
    user_data = resultado.get('user', {})
    return render_template('auth/profile.html', user=user_data)

@auth_bp.route('/profile', methods=['POST'])
@jwt_required
def update_profile():
    """Atualizar perfil do usuário"""
    user_id = request.jwt_user_id
    token = request.jwt_token
    
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    
    if not first_name:
        flash('Nome é obrigatório', 'error')
        return redirect(url_for('auth.profile'))
    
    resultado = auth_service.update_user(user_id, token, {
        'firstName': first_name,
        'lastName': last_name
    })
    
    if resultado['success']:
        flash(resultado['message'], 'success')
        # Atualizar sessão
        session['user'] = resultado.get('user', {})
    else:
        flash(resultado['message'], 'error')
    
    return redirect(url_for('auth.profile'))

# API endpoints
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API de login para requisições AJAX"""
    data = request.get_json()
    
    if not data or 'email' not in data or 'senha' not in data:
        return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'}), 400
    
    email = data['email'].strip()
    senha = data['senha']
    
    resultado = auth_service.login(email, senha, request.remote_addr)
    
    if resultado['success']:
        return jsonify(resultado)
    else:
        return jsonify(resultado), 401

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """API de cadastro para requisições AJAX"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
    
    nome = data.get('nome', '').strip()
    email = data.get('email', '').strip()
    senha = data.get('senha', '')
    
    # Separar nome e sobrenome
    partes_nome = nome.split(' ', 1)
    first_name = partes_nome[0]
    last_name = partes_nome[1] if len(partes_nome) > 1 else ''
    
    # Validações
    if not nome or not email or not senha:
        return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
    
    if len(senha) < 12:
        return jsonify({'success': False, 'message': 'A senha deve ter pelo menos 12 caracteres'}), 400
    
    resultado = auth_service.register(email, senha, first_name, last_name)
    
    if resultado['success']:
        return jsonify(resultado)
    else:
        return jsonify(resultado), 400

@auth_bp.route('/api/check-email', methods=['POST'])
def check_email():
    """Verifica se email já está cadastrado (delegado ao modulo-auth)"""
    # O modulo-auth verifica email durante o registro
    return jsonify({'available': True, 'message': 'Email será verificado no registro'})

@auth_bp.route('/api/refresh', methods=['POST'])
def api_refresh():
    """API para renovar token de acesso"""
    data = request.get_json()
    
    if not data or 'refresh_token' not in data:
        return jsonify({'success': False, 'message': 'Refresh token é obrigatório'}), 400
    
    refresh_token = data['refresh_token']
    
    resultado = auth_service.refresh_token(refresh_token)
    
    if resultado['success']:
        return jsonify(resultado)
    else:
        return jsonify(resultado), 401
