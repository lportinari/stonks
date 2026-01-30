from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from typing import Dict, List
import logging
from services.ranking_service import RankingService
from services.fundamentus_scraper import FundamentusScraper
from services.cache_manager import CacheManager, CacheKeys
from services.indicator_calculator import IndicatorCalculator
from config import Config

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

ranking_service = RankingService()
scraper = FundamentusScraper()
cache_manager = CacheManager()
calculator = IndicatorCalculator()

@main_bp.route('/')
def index():
    """Página principal com o ranking de ações"""
    try:
        # Obter parâmetros de filtro
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', Config.STOCKS_PER_PAGE, type=int)
        sector_filter = request.args.get('sector')
        
        # Tentar obter do cache primeiro
        cache_key = f"ranking_page_{page}_{per_page}_{sector_filter or 'all'}"
        cached_data = cache_manager.get(cache_key)
        
        if cached_data:
            stocks_data = cached_data['stocks']
            sectors = cached_data['sectors']
            stats = cached_data['stats']
        else:
            # Obter dados do serviço com paginação real
            if sector_filter:
                stocks_data = ranking_service.get_sector_ranking(sector_filter, limit=per_page)
            else:
                stocks_data = ranking_service.get_current_ranking(page=page, per_page=per_page)
            
            # Obter setores disponíveis
            sectors = ranking_service.get_available_sectors()
            
            # Obter estatísticas
            stats = ranking_service.get_ranking_statistics()
            
            # Salvar no cache
            cache_data = {
                'stocks': [stock.to_dict() for stock in stocks_data],
                'sectors': sectors,
                'stats': stats
            }
            cache_manager.set(cache_key, cache_data)
        
        return render_template('index.html', 
                             stocks=stocks_data,
                             sectors=sectors,
                             current_sector=sector_filter,
                             stats=stats,
                             page=page,
                             per_page=per_page)
    
    except Exception as e:
        logger.error(f"Erro na página principal: {e}")
        flash('Erro ao carregar dados. Tente novamente mais tarde.', 'error')
        return render_template('index.html', stocks=[], sectors=[], stats={})

@main_bp.route('/stock/<ticker>')
def stock_detail(ticker):
    """Página de detalhes de uma ação específica - redireciona para versão funcional"""
    # Redirecionar para a versão funcional via API
    return redirect(f'/api/stock/{ticker}')

@main_bp.route('/detail/<ticker>')
def stock_detail_working(ticker):
    """Versão funcional da página de detalhes"""
    try:
        logger.info(f"Buscando detalhes da ação {ticker}")
        
        # Buscar ação via API interna
        stock = ranking_service.get_stock_by_ticker(ticker)
        if not stock:
            return f"<h1>Ação {ticker} não encontrada</h1><p><a href='/'>Voltar</a></p>"
        
        # Página HTML simples inline
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>{stock.ticker} - {stock.empresa}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
                    <div class="container">
                        <a class="navbar-brand" href="/">
                            <i class="fas fa-chart-line"></i> Stonks
                        </a>
                    </div>
                </nav>
                
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h3>{stock.ticker} - {stock.empresa}</h3>
                        <small class="text-white-50">Setor: {stock.setor or 'Não classificado'}</small>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Valuation</h6>
                                <p><strong>Cotação:</strong> R$ {stock.cotacao:.2f if stock.cotacao else '--'}</p>
                                <p><strong>P/L:</strong> {stock.pl:.2f if stock.pl else '--'}</p>
                                <p><strong>P/VP:</strong> {stock.pvp:.2f if stock.pvp else '--'}</p>
                                <p><strong>PSR:</strong> {stock.psr:.2f if stock.psr else '--'}</p>
                            </div>
                            <div class="col-md-6">
                                <h6>Rentabilidade</h6>
                                <p><strong>DY:</strong> {stock.div_yield * 100:.2f if stock.div_yield else '--'}%</p>
                                <p><strong>ROE:</strong> {stock.roe * 100:.2f if stock.roe else '--'}%</p>
                                <p><strong>ROIC:</strong> {stock.roic * 100:.2f if stock.roic else '--'}%</p>
                                <p><strong>Margem Líquida:</strong> {stock.margem_liquida * 100:.2f if stock.margem_liquida else '--'}%</p>
                            </div>
                        </div>
                        
                        <div class="row mt-3">
                            <div class="col-md-6">
                                <h6>Ranking</h6>
                                <p><strong>Score Final:</strong> {stock.score_final:.1f if stock.score_final else '--'}/100</p>
                                <p><strong>Posição:</strong> #{stock.rank_posicao if stock.rank_posicao else '--'}</p>
                            </div>
                            <div class="col-md-6">
                                <h6>Informações</h6>
                                <p><strong>Fonte:</strong> {stock.fonte_dados or 'Não informada'}</p>
                                <p><strong>Atualização:</strong> {stock.data_atualizacao or 'Não informada'}</p>
                            </div>
                        </div>
                        
                        <hr>
                        <div class="row">
                            <div class="col-12">
                                <a href="/" class="btn btn-primary me-2">
                                    <i class="fas fa-arrow-left"></i> Voltar ao Ranking
                                </a>
                                <a href="/api/stock/{ticker}" target="_blank" class="btn btn-outline-secondary">
                                    <i class="fas fa-code"></i> Ver JSON (API)
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        logger.info(f"Página de detalhes gerada para {ticker}")
        return html
    
    except Exception as e:
        logger.error(f"Erro nos detalhes da ação {ticker}: {e}", exc_info=True)
        return f"<h1>Erro: {str(e)}</h1><p><a href='/'>Voltar</a></p>"

@main_bp.route('/compare')
def compare():
    """Página de comparação de ações"""
    try:
        # Obter tickers da query string
        tickers = request.args.get('tickers', '').split(',')
        tickers = [t.strip().upper() for t in tickers if t.strip()]
        
        if len(tickers) < 2:
            flash('Selecione pelo menos 2 ações para comparar.', 'warning')
            return redirect(url_for('main.index'))
        
        if len(tickers) > 5:
            flash('Máximo de 5 ações por comparação.', 'warning')
            tickers = tickers[:5]
        
        # Obter dados das ações
        comparison_data = ranking_service.compare_stocks(tickers)
        
        return render_template('compare.html', 
                             stocks=comparison_data,
                             tickers=tickers)
    
    except Exception as e:
        logger.error(f"Erro na comparação: {e}")
        flash('Erro ao comparar ações.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/config')
def config():
    """Página de configuração dos pesos do ranking"""
    try:
        # Obter pesos atuais (por enquanto usar padrão)
        current_weights = Config.DEFAULT_WEIGHTS.copy()
        
        return render_template('config.html', weights=current_weights)
    
    except Exception as e:
        logger.error(f"Erro na página de configuração: {e}")
        flash('Erro ao carregar configuração.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/config', methods=['POST'])
def update_config():
    """Atualiza os pesos do ranking"""
    try:
        # Obter pesos do formulário
        weights = {}
        weight_fields = ['dy', 'pl', 'pvp', 'roe', 'margem_liquida']
        
        total_weight = 0
        for field in weight_fields:
            weight = request.form.get(f'weight_{field}', type=float)
            if weight is not None and weight >= 0:
                weights[field] = weight
                total_weight += weight
        
        # Validar soma dos pesos
        if abs(total_weight - 1.0) > 0.01:
            flash('A soma dos pesos deve ser igual a 1.0 (100%).', 'error')
            return redirect(url_for('main.config'))
        
        # Atualizar ranking com novos pesos
        updated_count = ranking_service.update_ranking(weights)
        
        # Limpar cache relacionado
        cache_manager.invalidate(CacheKeys.RANKING_DATA)
        cache_manager.invalidate(CacheKeys.TOP_STOCKS)
        
        flash(f'Configuração atualizada! {updated_count} ações reprocessadas.', 'success')
        return redirect(url_for('main.index'))
    
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração: {e}")
        flash('Erro ao atualizar configuração.', 'error')
        return redirect(url_for('main.config'))

@main_bp.route('/filter', methods=['GET', 'POST'])
def filter_stocks():
    """Página de filtros avançados"""
    if request.method == 'GET':
        return render_template('filter.html', sectors=ranking_service.get_available_sectors())
    
    try:
        # Obter critérios do formulário
        min_dy = request.form.get('min_dy', type=float)
        max_pl = request.form.get('max_pl', type=float)
        max_pvp = request.form.get('max_pvp', type=float)
        min_roe = request.form.get('min_roe', type=float)
        sector = request.form.get('sector')
        
        # Aplicar filtros
        filtered_stocks = ranking_service.filter_stocks(
            min_dy=min_dy,
            max_pl=max_pl,
            max_pvp=max_pvp,
            min_roe=min_roe,
            sector=sector,
            limit=100
        )
        
        return render_template('filter_results.html', 
                             stocks=filtered_stocks,
                             criteria={
                                 'min_dy': min_dy,
                                 'max_pl': max_pl,
                                 'max_pvp': max_pvp,
                                 'min_roe': min_roe,
                                 'sector': sector
                             })
    
    except Exception as e:
        logger.error(f"Erro nos filtros: {e}")
        flash('Erro ao aplicar filtros.', 'error')
        return redirect(url_for('main.filter'))

@main_bp.route('/update-data')
def update_data():
    """Atualiza dados das ações (manual)"""
    try:
        # Implementar atualização manual dos dados
        flash('Atualização de dados em desenvolvimento.', 'info')
        return redirect(url_for('main.index'))
    
    except Exception as e:
        logger.error(f"Erro na atualização de dados: {e}")
        flash('Erro ao atualizar dados.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/about')
def about():
    """Página sobre o projeto"""
    return render_template('about.html')

# Tratamento de erros
@main_bp.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno: {error}")
    return render_template('500.html'), 500