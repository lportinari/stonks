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
        asset_class_filter = request.args.get('asset_class')
        search_filter = request.args.get('search')
        
        # Desabilitar cache temporariamente para garantir paginação funcionando
        # TODO: Implementar cache inteligente que respeita paginação
        
        # Obter dados do serviço com paginação real e todos os filtros
        stocks_data = ranking_service.get_current_ranking(
            page=page, 
            per_page=per_page, 
            sector_filter=sector_filter, 
            asset_class_filter=asset_class_filter,
            search_filter=search_filter
        )
        
        # Obter setores disponíveis
        sectors = ranking_service.get_available_sectors()
        
        # Obter estatísticas
        stats = ranking_service.get_ranking_statistics()
        
        return render_template('index.html', 
                             stocks=stocks_data,
                             sectors=sectors,
                             current_sector=sector_filter,
                             current_asset_class=asset_class_filter,
                             current_search=search_filter,
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
    """Versão funcional da página de detalhes com indicadores enriquecidos"""
    try:
        logger.info(f"Buscando detalhes da ação {ticker}")
        
        # Buscar ação via API interna
        stock = ranking_service.get_stock_by_ticker(ticker)
        if not stock:
            return f"<h1>Ação {ticker} não encontrada</h1><p><a href='/'>Voltar</a></p>"
        
        # Importar serviços para cálculos avançados
        from services.indicator_enricher import IndicatorEnricher
        from services.pl_calculator import PLCalculator
        from services.logo_service import LogoService
        from models.database import SessionLocal
        
        # Inicializar serviços
        db_session = SessionLocal()
        enricher = IndicatorEnricher(db_session)
        pl_calculator = PLCalculator(db_session)
        logo_service = LogoService(db_session)
        
        # Obter logo
        logo_url = logo_service.get_logo_url(ticker) or stock.logo_url
        
        # Calcular indicadores enriquecidos
        roic_advanced = enricher.calculate_roic_advanced(stock)
        peg_ratio = enricher.calculate_peg_ratio(stock)
        graham_number = enricher.calculate_graham_number(stock)
        altman_z = enricher.calculate_altman_z_score(stock)
        magic_rank = enricher.calculate_magic_formula_rank(stock)
        beneish_m = enricher.calculate_beneish_m_score(stock)
        earnings_yield = enricher.calculate_earnings_yield(stock)
        
        # Obter sinais de análise
        sinais = enricher._generate_signals(stock)
        
        # Preparar dados formatados com tratamento seguro para None
        cotacao_fmt = f"R$ {stock.cotacao:.2f}" if stock.cotacao is not None else "--"
        pl_fmt = f"{stock.pl:.2f}" if stock.pl is not None else "--"
        pvp_fmt = f"{stock.pvp:.2f}" if stock.pvp is not None else "--"
        psr_fmt = f"{stock.psr:.2f}" if stock.psr is not None else "--"
        dy_fmt = f"{stock.div_yield * 100:.2f}%" if stock.div_yield is not None else "--"
        roe_fmt = f"{stock.roe * 100:.2f}%" if stock.roe is not None else "--"
        roic_fmt = f"{stock.roic * 100:.2f}%" if stock.roic is not None else "--"
        margem_fmt = f"{stock.margem_liquida * 100:.2f}%" if stock.margem_liquida is not None else "--"
        score_fmt = f"{stock.score_final:.1f}/100" if stock.score_final is not None else "--/100"
        posicao_fmt = f"#{stock.rank_posicao}" if stock.rank_posicao is not None else "--"
        
        # Formatar indicadores enriquecidos
        roic_adv_fmt = f"{roic_advanced:.2f}%" if roic_advanced is not None else "--"
        peg_fmt = f"{peg_ratio:.2f}" if peg_ratio is not None else "--"
        graham_fmt = f"R$ {graham_number:.2f}" if graham_number is not None else "--"
        
        # Calcular valores de risco antes de formatar
        altman_z_formatted = f"{altman_z:.2f}" if altman_z is not None else "--"
        altman_risco = "BAIXO" if altman_z is not None and altman_z > 3 else "MODERADO" if altman_z is not None and altman_z > 1.8 else "ALTO" if altman_z is not None else "--"
        
        magic_rank_formatted = f"{magic_rank}" if magic_rank is not None else "--"
        magic_class = "EXCELENTE" if magic_rank is not None and magic_rank <= 10 else "BOM" if magic_rank is not None and magic_rank <= 30 else "REGULAR" if magic_rank is not None else "--"
        
        beneish_m_formatted = f"{beneish_m:.2f}" if beneish_m is not None else "--"
        beneish_risco = "POSSÍVEL" if beneish_m is not None and beneish_m > -1.78 else "POUCO PROVÁVEL" if beneish_m is not None else "--"
        
        ey_fmt = f"{earnings_yield:.2f}%" if earnings_yield is not None else "--"
        
        # Calcular margem de segurança do Graham
        margem_seguranca = ""
        if graham_number is not None and stock.cotacao is not None:
            margem = ((graham_number - stock.cotacao) / stock.cotacao * 100)
            margem_seguranca = f"{margem:.1f}%"
        
        # Badge da classe de ativo
        asset_class_badge = {
            'acao': 'bg-primary',
            'fii': 'bg-success', 
            'etf': 'bg-info',
            'bdr': 'bg-warning'
        }.get(stock.asset_class, 'bg-secondary')
        
        # Página HTML completa com tratamento seguro para valores None
        stock_ticker = stock.ticker or 'N/A'
        stock_empresa = stock.empresa or 'N/A'
        stock_setor = stock.setor or 'Não classificado'
        stock_subsetor = stock.subsetor or '--'
        stock_data_atualizacao = stock.data_atualizacao or 'Sem data'
        stock_fonte_dados = stock.fonte_dados or '--'
        stock_liquidity = stock.liquidity or '--'
        
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{stock_ticker} - {stock_empresa}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <style>
                .stock-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .indicator-card {{ transition: transform 0.2s; }}
                .indicator-card:hover {{ transform: translateY(-2px); }}
                .signal-buy {{ color: #28a745; font-weight: bold; }}
                .signal-sell {{ color: #dc3545; font-weight: bold; }}
                .signal-neutral {{ color: #6c757d; }}
                .signal-excellent {{ color: #007bff; font-weight: bold; }}
                .signal-good {{ color: #28a745; font-weight: bold; }}
                .signal-poor {{ color: #dc3545; font-weight: bold; }}
                .logo-img {{ width: 64px; height: 64px; object-fit: contain; }}
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container">
                    <a class="navbar-brand" href="/">
                        <i class="fas fa-chart-line"></i> Stonks
                    </a>
                </div>
            </nav>
            
            <div class="container mt-4">
                <div class="card shadow-lg">
                    <div class="card-header stock-header text-white">
                        <div class="row align-items-center">
                            <div class="col-md-8">
                                <h3 class="mb-0">{stock_ticker}</h3>
                                <h5 class="mb-1">{stock_empresa}</h5>
                                <div class="d-flex gap-2 align-items-center">
                                    <span class="badge {asset_class_badge}">{stock.asset_class.upper() if stock.asset_class else 'AÇÃO'}</span>
                                    <small><i class="fas fa-industry"></i> {stock_setor}</small>
                                </div>
                            </div>
                            <div class="col-md-4 text-end">
                                {f'<img src="{logo_url}" class="logo-img" alt="{stock_ticker}">' if logo_url else ''}
                            </div>
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <!-- Resumo Rápido -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="card indicator-card h-100">
                                    <div class="card-body text-center">
                                        <h6 class="text-muted">Cotação</h6>
                                        <h4 class="text-primary">{cotacao_fmt}</h4>
                                        <small class="text-muted">{stock_data_atualizacao}</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card indicator-card h-100">
                                    <div class="card-body text-center">
                                        <h6 class="text-muted">Score Final</h6>
                                        <h4 class="{'text-success' if stock.score_final is not None and stock.score_final >= 70 else 'text-warning' if stock.score_final is not None and stock.score_final >= 40 else 'text-danger'}">{score_fmt}</h4>
                                        <small class="text-muted">{posicao_fmt}</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card indicator-card h-100">
                                    <div class="card-body text-center">
                                        <h6 class="text-muted">Dividend Yield</h6>
                                        <h4 class="text-info">{dy_fmt}</h4>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card indicator-card h-100">
                                    <div class="card-body text-center">
                                        <h6 class="text-muted">P/L</h6>
                                        <h4 class="{'text-success' if stock.pl is not None and stock.pl < 10 else 'text-warning' if stock.pl is not None and stock.pl < 15 else 'text-danger'}">{pl_fmt}</h4>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Indicadores Fundamentais -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5><i class="fas fa-chart-line"></i> Indicadores Fundamentais</h5>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>P/VP</h6>
                                        <p class="h5">{pvp_fmt}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>PSR</h6>
                                        <p class="h5">{psr_fmt}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>ROE</h6>
                                        <p class="h5">{roe_fmt}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>ROIC</h6>
                                        <p class="h5">{roic_fmt}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>Margem Líquida</h6>
                                        <p class="h5">{margem_fmt}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Indicadores Avançados -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5><i class="fas fa-brain"></i> Indicadores Avançados</h5>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <div class="card border-info">
                                    <div class="card-body">
                                        <h6>ROIC Avançado</h6>
                                        <p class="h5 text-info">{roic_adv_fmt}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>PEG Ratio</h6>
                                        <p class="h5">{peg_fmt}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card border-success">
                                    <div class="card-body">
                                        <h6>Número de Graham</h6>
                                        <p class="h5 text-success">{graham_fmt}</p>
                                        <small class="text-muted">Margem: {margem_seguranca}</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>Earnings Yield</h6>
                                        <p class="h5">{ey_fmt}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Análise de Risco -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5><i class="fas fa-shield-alt"></i> Análise de Risco</h5>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <div class="card border-warning">
                                    <div class="card-body">
                                        <h6>Altman Z-Score</h6>
                                        <p class="h5">{altman_z_formatted}</p>
                                        <span class="badge bg-warning text-dark">Risco {altman_risco}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>Magic Formula</h6>
                                        <p class="h5">{magic_rank_formatted}/100</p>
                                        <span class="badge bg-info">{magic_class}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <div class="card border-danger">
                                    <div class="card-body">
                                        <h6>Beneish M-Score</h6>
                                        <p class="h5">{beneish_m_formatted}</p>
                                        <span class="badge bg-danger text-white">Manipulação {beneish_risco}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Sinais de Compra/Venda -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5><i class="fas fa-lightbulb"></i> Sinais de Análise</h5>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>Valuation</h6>
                                        <p><i class="fas fa-chart-line"></i> <strong>P/L:</strong> 
                                           <span class="{'signal-buy' if sinais.get('pl') == 'COMPRA (barato)' else 'signal-sell' if sinais.get('pl') == 'VENDA (caro)' else 'signal-neutral'}">{sinais.get('pl', '--')}</span></p>
                                        <p><i class="fas fa-chart-pie"></i> <strong>P/VP:</strong> 
                                           <span class="{'signal-buy' if sinais.get('pvp') == 'COMPRA (desconto)' else 'signal-sell' if sinais.get('pvp') == 'VENDA (premium alto)' else 'signal-neutral'}">{sinais.get('pvp', '--')}</span></p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>Rentabilidade</h6>
                                        <p><i class="fas fa-percentage"></i> <strong>ROE:</strong> 
                                           <span class="{'signal-excellent' if sinais.get('roe') == 'EXCELENTE' else 'signal-good' if sinais.get('roe') == 'BOM' else 'signal-poor'}">{sinais.get('roe', '--')}</span></p>
                                        <p><i class="fas fa-percentage"></i> <strong>ROIC:</strong> 
                                           <span class="{'signal-excellent' if sinais.get('roic') == 'EXCELENTE' else 'signal-good' if sinais.get('roic') == 'BOM' else 'signal-poor'}">{sinais.get('roic', '--')}</span></p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>Risco</h6>
                                        <p><i class="fas fa-shield-alt"></i> <strong>Risco:</strong> 
                                           <span class="{'signal-excellent' if sinais.get('risco') == 'BAIXO' else 'signal-poor' if sinais.get('risco') == 'ALTO' else 'signal-neutral'}">{sinais.get('risco', '--')}</span></p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Informações Adicionais -->
                        <div class="row">
                            <div class="col-12">
                                <div class="card">
                                    <div class="card-body">
                                        <h6>Informações Adicionais</h6>
                                        <div class="row">
                                            <div class="col-md-6">
                                                <p><strong>Subsetor:</strong> {stock_subsetor}</p>
                                                <p><strong>Valor de Mercado:</strong> {f"R$ {stock.valor_mercado:,.0f}M" if stock.valor_mercado is not None else '--'}</p>
                                                <p><strong>Patrimônio Líquido:</strong> {f"R$ {stock.patrimonio_liquido:,.0f}M" if stock.patrimonio_liquido is not None else '--'}</p>
                                            </div>
                                            <div class="col-md-6">
                                                <p><strong>Fonte dos Dados:</strong> {stock.fonte_dados or '--'}</p>
                                                <p><strong>Volume:</strong> {f"{stock.volume:,.0f}" if stock.volume is not None else '--'}</p>
                                                <p><strong>Liquidez:</strong> {stock.liquidity or '--'}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Ações -->
                        <hr>
                        <div class="row">
                            <div class="col-12 text-center">
                                <a href="/" class="btn btn-primary btn-lg me-2">
                                    <i class="fas fa-arrow-left"></i> Voltar ao Ranking
                                </a>
                                <a href="/api/stock/{ticker}" target="_blank" class="btn btn-outline-secondary btn-lg">
                                    <i class="fas fa-code"></i> Ver JSON (API)
                                </a>
                                <button onclick="window.print()" class="btn btn-outline-info btn-lg">
                                    <i class="fas fa-print"></i> Imprimir Relatório
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Adicionar tooltips
                document.addEventListener('DOMContentLoaded', function() {{
                    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                    tooltipTriggerList.map(function (tooltipTriggerEl) {{
                        return new bootstrap.Tooltip(tooltipTriggerEl);
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        logger.info(f"Página de detalhes enriquecida gerada para {ticker}")
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