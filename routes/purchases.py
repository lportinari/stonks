from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from services.purchase_service import PurchaseService
from services.ranking_service import RankingService
from services.jwt_validator import jwt_required, get_current_user_id
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

purchases_bp = Blueprint('purchases', __name__, url_prefix='/purchases')

purchase_service = PurchaseService()
ranking_service = RankingService()

@purchases_bp.route('/')
@jwt_required
def index():
    """Listagem de compras do usuário"""
    try:
        # Obter filtros da query string
        filtros = {
            'ticker': request.args.get('ticker', ''),
            'data_inicio': request.args.get('data_inicio', ''),
            'data_fim': request.args.get('data_fim', ''),
            'ativos_vendidos': request.args.get('ativos_vendidos', ''),
            'ordenacao': request.args.get('ordenacao', 'data_compra_desc'),
            'page': request.args.get('page', 1, type=int),
            'per_page': request.args.get('per_page', 20, type=int)
        }
        
        # Processar ordenação
        order_by = 'data_compra'
        order_dir = 'DESC'
        
        if filtros['ordenacao']:
            if filtros['ordenacao'] == 'data_compra_asc':
                order_by, order_dir = 'data_compra', 'ASC'
            elif filtros['ordenacao'] == 'data_compra_desc':
                order_by, order_dir = 'data_compra', 'DESC'
            elif filtros['ordenacao'] == 'ticker_asc':
                order_by, order_dir = 'ticker', 'ASC'
            elif filtros['ordenacao'] == 'valor_desc':
                order_by, order_dir = 'custo_total', 'DESC'
        
        # Buscar compras
        user_id = get_current_user_id()
        resultado = purchase_service.listar_compras(
            user_id,
            page=filtros['page'], 
            per_page=filtros['per_page'],
            order_by=order_by,
            order_dir=order_dir,
            ticker_filter=filtros['ticker'] if filtros['ticker'] else None
        )
        
        if resultado['success']:
            purchases = resultado['compras']
            pagination = resultado['pagination']
            # Garantir que pagination tenha todos os atributos necessários
            if isinstance(pagination, dict):
                pagination.setdefault('pages', pagination.get('total_pages', 0))
                pagination.setdefault('total_pages', pagination.get('total_pages', 0))
        else:
            flash(resultado['message'], 'error')
            purchases = []
            pagination = {'page': 1, 'per_page': 20, 'total': 0, 'total_pages': 0, 'pages': 0}
        
        return render_template('purchases/index.html', 
                             purchases=purchases,
                             pagination=pagination,
                             filtros=filtros)
        
    except Exception as e:
        logger.error(f"Erro na listagem de compras: {e}")
        flash('Erro ao carregar compras.', 'error')
        filtros = {
            'ticker': '',
            'data_inicio': '',
            'data_fim': '',
            'ativos_vendidos': '',
            'ordenacao': 'data_compra_desc',
            'page': 1,
            'per_page': 20
        }
        pagination = {'page': 1, 'per_page': 20, 'total': 0, 'total_pages': 0, 'pages': 0}
        return render_template('purchases/index.html', purchases=[], pagination=pagination, filtros=filtros)

@purchases_bp.route('/new', methods=['GET', 'POST'])
@jwt_required
def new_purchase():
    """Formulário de nova compra"""
    if request.method == 'GET':
        return render_template('purchases/new_purchase.html', dados={}, edit_mode=False)
    
    if request.method == 'POST':
        dados = {
            'ticker': request.form.get('ticker', '').strip().upper(),
            'nome_ativo': request.form.get('nome_ativo', f"{request.form.get('ticker', '').strip()} - Manual"),
            'preco_unitario': request.form.get('preco_unitario', '').replace(',', '.'),
            'quantidade': request.form.get('quantidade', ''),
            'data_compra': request.form.get('data_compra', ''),
            'classe_ativo': request.form.get('classe_ativo', ''),
            'taxa_corretagem': request.form.get('taxa_corretagem', '0').replace(',', '.'),
            'taxa_emolumentos': request.form.get('taxa_emolumentos', '0').replace(',', '.'),
            'outros_custos': request.form.get('outros_custos', '0').replace(',', '.'),
            'notas': request.form.get('notas', '').strip()
        }
        
        # Validações básicas
        if not dados['ticker'] or not dados['preco_unitario'] or not dados['quantidade'] or not dados['data_compra']:
            flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
            return render_template('purchases/new_purchase.html', dados=dados, edit_mode=False)
        
        try:
            # Converter valores
            dados['preco_unitario'] = float(dados['preco_unitario'])
            dados['quantidade'] = int(dados['quantidade'])
            dados['taxa_corretagem'] = float(dados['taxa_corretagem'])
            dados['taxa_emolumentos'] = float(dados['taxa_emolumentos'])
            dados['outros_custos'] = float(dados['outros_custos'])
            
            if dados['preco_unitario'] <= 0 or dados['quantidade'] <= 0:
                flash('Preço e quantidade devem ser maiores que zero', 'error')
                return render_template('purchases/new_purchase.html', dados=dados, edit_mode=False)
            
            # Criar compra
            user_id = get_current_user_id()
            resultado = purchase_service.criar_compra(
                user_id=user_id,
                ticker=dados['ticker'],
                nome_ativo=dados['nome_ativo'],
                quantidade=dados['quantidade'],
                preco_unitario=dados['preco_unitario'],
                taxas=dados['taxa_corretagem'] + dados['taxa_emolumentos'] + dados['outros_custos'],
                data_compra=datetime.strptime(dados['data_compra'], '%Y-%m-%d').date(),
                classe_ativo=dados['classe_ativo'] if dados['classe_ativo'] else None
            )
            
            if resultado['success']:
                flash(resultado['message'], 'success')
                return redirect(url_for('purchases.index'))
            else:
                flash(resultado['message'], 'error')
                
        except ValueError:
            flash('Valores numéricos inválidos', 'error')
        
        return render_template('purchases/new_purchase.html', dados=dados, edit_mode=False)

@purchases_bp.route('/<int:purchase_id>')
@jwt_required
def view_purchase(purchase_id):
    """Visualizar detalhes de uma compra"""
    user_id = get_current_user_id()
    resultado = purchase_service.obter_compra(purchase_id, user_id)
    
    if resultado['success']:
        return render_template('purchases/view.html', purchase=resultado['purchase'])
    else:
        flash(resultado['message'], 'error')
        return redirect(url_for('purchases.index'))

@purchases_bp.route('/<int:purchase_id>/edit', methods=['GET', 'POST'])
@jwt_required
def edit_purchase(purchase_id):
    """Editar dados de uma compra"""
    user_id = get_current_user_id()
    resultado = purchase_service.obter_compra(purchase_id, user_id)
    
    if not resultado['success']:
        flash(resultado['message'], 'error')
        return redirect(url_for('purchases.index'))
    
    purchase = resultado['purchase']
    
    if request.method == 'POST':
        dados = {
            'nome_ativo': request.form.get('nome_ativo', '').strip(),
            'taxa_corretagem': request.form.get('taxa_corretagem', '0').replace(',', '.'),
            'taxa_emolumentos': request.form.get('taxa_emolumentos', '0').replace(',', '.'),
            'outros_custos': request.form.get('outros_custos', '0').replace(',', '.'),
            'notas': request.form.get('notas', '').strip()
        }
        
        if not dados['nome_ativo']:
            flash('Nome do ativo é obrigatório', 'error')
        return render_template('purchases/new_purchase.html', dados=purchase, edit_mode=True, purchase_id=purchase_id)
        
        try:
            # Converter valores
            dados['taxa_corretagem'] = float(dados['taxa_corretagem'])
            dados['taxa_emolumentos'] = float(dados['taxa_emolumentos'])
            dados['outros_custos'] = float(dados['outros_custos'])
            
            # Atualizar compra
            user_id = get_current_user_id()
            resultado = purchase_service.atualizar_compra(user_id, purchase_id, dados)
            
            if resultado['success']:
                flash(resultado['message'], 'success')
                return redirect(url_for('purchases.view_purchase', purchase_id=purchase_id))
            else:
                flash(resultado['message'], 'error')
                
        except ValueError:
            flash('Valores numéricos inválidos', 'error')
        
        return render_template('purchases/new_purchase.html', dados=purchase, edit_mode=True, purchase_id=purchase_id)
    
    return render_template('purchases/new_purchase.html', dados=purchase, edit_mode=True, purchase_id=purchase_id)

@purchases_bp.route('/<int:purchase_id>/sell', methods=['GET', 'POST'])
@jwt_required
def sell_purchase(purchase_id):
    """Registrar venda de ativos"""
    user_id = get_current_user_id()
    resultado = purchase_service.obter_compra(purchase_id, user_id)
    
    if not resultado['success']:
        flash(resultado['message'], 'error')
        return redirect(url_for('purchases.index'))
    
    purchase = resultado['purchase']
    
    if purchase['quantidade_restante'] <= 0:
        flash('Não há ativos disponíveis para venda', 'error')
        return redirect(url_for('purchases.view_purchase', purchase_id=purchase_id))
    
    if request.method == 'POST':
        dados = {
            'quantidade': request.form.get('quantidade', ''),
            'preco_unitario': request.form.get('preco_unitario', '').replace(',', '.'),
            'taxa_corretagem': request.form.get('taxa_corretagem', '0').replace(',', '.'),
            'taxa_emolumentos': request.form.get('taxa_emolumentos', '0').replace(',', '.')
        }
        
        # Validações
        if not dados['quantidade'] or not dados['preco_unitario']:
            flash('Quantidade e preço são obrigatórios', 'error')
            return render_template('purchases/sell.html', purchase=purchase, dados=dados)
        
        try:
            dados['quantidade'] = int(dados['quantidade'])
            dados['preco_unitario'] = float(dados['preco_unitario'])
            dados['taxa_corretagem'] = float(dados['taxa_corretagem'])
            dados['taxa_emolumentos'] = float(dados['taxa_emolumentos'])
            
            if dados['quantidade'] <= 0 or dados['preco_unitario'] <= 0:
                flash('Valores devem ser maiores que zero', 'error')
                return render_template('purchases/sell.html', purchase=purchase, dados=dados)
            
            if dados['quantidade'] > purchase['quantidade_restante']:
                flash(f'Quantidade máxima para venda: {purchase["quantidade_restante"]}', 'error')
                return render_template('purchases/sell.html', purchase=purchase, dados=dados)
            
            # Registrar venda
            user_id = get_current_user_id()
            resultado = purchase_service.registrar_venda(user_id, purchase_id, dados)
            
            if resultado['success']:
                flash(resultado['message'], 'success')
                return redirect(url_for('purchases.view_purchase', purchase_id=purchase_id))
            else:
                flash(resultado['message'], 'error')
                
        except ValueError:
            flash('Valores numéricos inválidos', 'error')
        
        return render_template('purchases/sell.html', purchase=purchase, dados=dados)
    
    return render_template('purchases/sell.html', purchase=purchase, dados={})

@purchases_bp.route('/<int:purchase_id>/delete', methods=['POST'])
@jwt_required
def delete_purchase(purchase_id):
    """Excluir uma compra"""
    user_id = get_current_user_id()
    resultado = purchase_service.excluir_compra(purchase_id, user_id)
    
    if resultado['success']:
        flash(resultado['message'], 'success')
    else:
        flash(resultado['message'], 'error')
    
    return redirect(url_for('purchases.index'))

@purchases_bp.route('/dashboard')
@jwt_required
def dashboard():
    """Dashboard do portfolio"""
    try:
        # Buscar dados do dashboard
        user_id = get_current_user_id()
        resultado_dashboard = purchase_service.get_dashboard_data(user_id)
        
        if resultado_dashboard['success']:
            portfolio = resultado_dashboard['resumo']
            distribuicao = resultado_dashboard['distribuicao']
            performance = resultado_dashboard['performance']
            compras_recentes = resultado_dashboard['compras_recentes']
        else:
            flash(resultado_dashboard['message'], 'error')
            portfolio = {
                'total_investido': 0,
                'valor_atual': 0,
                'resultado_total': 0,
                'rentabilidade_total': 0,
                'posicoes': [],
                'analise_setor': {}
            }
            distribuicao = []
            performance = {}
            compras_recentes = []
        
        return render_template('purchases/dashboard.html', 
                             portfolio=portfolio,
                             distribuicao=distribuicao,
                             performance=performance,
                             compras_recentes=compras_recentes)
        
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        flash('Erro ao carregar dashboard.', 'error')
        return redirect(url_for('purchases.index'))

# API endpoints
@purchases_bp.route('/api/stock-info')
@jwt_required
def api_stock_info():
    """Busca informações de um ativo para autocomplete"""
    ticker = request.args.get('ticker', '').strip().upper()
    
    if not ticker:
        return jsonify({'success': False, 'message': 'Ticker não fornecido'})
    
    try:
        # Buscar no sistema de ranking
        stock = ranking_service.get_stock_by_ticker(ticker)
        
        if stock:
            return jsonify({
                'success': True,
                'data': {
                    'ticker': stock.ticker,
                    'nome_ativo': stock.empresa,
                    'setor': stock.setor,
                    'cotacao': stock.cotacao
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Ativo não encontrado'})
            
    except Exception as e:
        logger.error(f"Erro ao buscar info do ativo: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar informações'})

@purchases_bp.route('/api/search-stocks')
@jwt_required
def api_search_stocks():
    """Busca ações para autocomplete"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'success': True, 'results': []})
    
    try:
        # Buscar ações que contenham o query
        stocks = ranking_service.search_stocks(query, limit=10)
        
        results = []
        for stock in stocks:
            results.append({
                'ticker': stock.ticker,
                'nome': stock.empresa,
                'setor': stock.setor
            })
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        logger.error(f"Erro na busca de ações: {e}")
        return jsonify({'success': False, 'message': 'Erro na busca'})