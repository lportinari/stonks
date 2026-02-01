from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

auth_service = AuthService()

@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário para o Flask-Login"""
    return auth_service.get_usuario_by_id(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        lembrar = request.form.get('lembrar') == 'on'
        
        if not email or not senha:
            flash('Email e senha são obrigatórios', 'error')
            return render_template('auth/login.html')
        
        # Autenticar usuário
        resultado = auth_service.autenticar_usuario(email, senha, request.remote_addr)
        
        if resultado['success']:
            user = auth_service.get_usuario_by_id(resultado['user']['id'])
            login_user(user, remember=lembrar)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash(resultado['message'], 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de cadastro"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        # Validações básicas
        if not nome or not email or not senha:
            flash('Todos os campos são obrigatórios', 'error')
            return render_template('auth/register.html')
        
        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres', 'error')
            return render_template('auth/register.html')
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem', 'error')
            return render_template('auth/register.html')
        
        # Criar usuário
        resultado = auth_service.criar_usuario(nome, email, senha)
        
        if resultado['success']:
            flash(resultado['message'], 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(resultado['message'], 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Solicitar reset de senha"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Email é obrigatório', 'error')
            return render_template('auth/reset_password.html')
        
        resultado = auth_service.solicitar_reset_senha(email)
        
        if resultado['success']:
            flash(resultado['message'], 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(resultado['message'], 'error')
    
    return render_template('auth/reset_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    """Reset de senha com token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        if not nova_senha or not confirmar_senha:
            flash('Todos os campos são obrigatórios', 'error')
            return render_template('auth/reset_password_confirm.html', token=token)
        
        if len(nova_senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres', 'error')
            return render_template('auth/reset_password_confirm.html', token=token)
        
        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem', 'error')
            return render_template('auth/reset_password_confirm.html', token=token)
        
        resultado = auth_service.resetar_senha(token, nova_senha)
        
        if resultado['success']:
            flash(resultado['message'], 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(resultado['message'], 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_confirm.html', token=token)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verificar email com token"""
    resultado = auth_service.verificar_email_token(token)
    
    if resultado['success']:
        flash(resultado['message'], 'success')
    else:
        flash(resultado['message'], 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Perfil do usuário"""
    return render_template('auth/profile.html')

@auth_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """Atualizar perfil do usuário"""
    nome = request.form.get('nome', '').strip()
    
    if not nome:
        flash('Nome é obrigatório', 'error')
        return redirect(url_for('auth.profile'))
    
    resultado = auth_service.atualizar_usuario(current_user.id, {'nome': nome})
    
    if resultado['success']:
        flash(resultado['message'], 'success')
    else:
        flash(resultado['message'], 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Alterar senha do usuário"""
    senha_atual = request.form.get('senha_atual', '')
    nova_senha = request.form.get('nova_senha', '')
    confirmar_senha = request.form.get('confirmar_senha', '')
    
    if not senha_atual or not nova_senha or not confirmar_senha:
        flash('Todos os campos são obrigatórios', 'error')
        return redirect(url_for('auth.profile'))
    
    if len(nova_senha) < 6:
        flash('A nova senha deve ter pelo menos 6 caracteres', 'error')
        return redirect(url_for('auth.profile'))
    
    if nova_senha != confirmar_senha:
        flash('As novas senhas não coincidem', 'error')
        return redirect(url_for('auth.profile'))
    
    resultado = auth_service.alterar_senha(current_user.id, senha_atual, nova_senha)
    
    if resultado['success']:
        flash(resultado['message'], 'success')
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
    
    resultado = auth_service.autenticar_usuario(email, senha, request.remote_addr)
    
    if resultado['success']:
        user = auth_service.get_usuario_by_id(resultado['user']['id'])
        login_user(user)
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
    
    # Validações
    if not nome or not email or not senha:
        return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
    
    if len(senha) < 6:
        return jsonify({'success': False, 'message': 'A senha deve ter pelo menos 6 caracteres'}), 400
    
    resultado = auth_service.criar_usuario(nome, email, senha)
    
    if resultado['success']:
        return jsonify(resultado)
    else:
        return jsonify(resultado), 400

@auth_bp.route('/api/check-email', methods=['POST'])
def check_email():
    """Verifica se email já está cadastrado"""
    data = request.get_json()
    email = data.get('email', '').strip() if data else ''
    
    if not email:
        return jsonify({'available': False, 'message': 'Email é obrigatório'})
    
    # Verificar se email existe
    from models.user import user_exists
    
    if user_exists(email):
        return jsonify({'available': False, 'message': 'Email já cadastrado'})
    else:
        return jsonify({'available': True, 'message': 'Email disponível'})
