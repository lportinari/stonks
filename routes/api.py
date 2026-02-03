from flask import Blueprint, jsonify, request
from models.stock import Stock
from models.database import SessionLocal
from sqlalchemy import func

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/stocks/search')
def search_stocks():
    """API para buscar ações por ticker"""
    ticker = request.args.get('ticker', '').upper().strip()
    
    if not ticker or len(ticker) < 3:
        return jsonify({'success': False, 'message': 'Ticker inválido'})
    
    try:
        with SessionLocal() as db:
            # Buscar ação no banco usando ORM
            stock = db.query(Stock).filter(
                func.upper(Stock.ticker) == ticker
            ).order_by(Stock.data_atualizacao.desc()).first()
            
            if stock:
                # Formatar dados para resposta
                stock_data = {
                    'ticker': stock.ticker,
                    'nome': stock.empresa,
                    'setor': stock.setor,
                    'papel': stock.asset_class,
                    'cotacao': float(stock.cotacao) if stock.cotacao else None,
                    'pl': float(stock.pl) if stock.pl else None,
                    'roic': float(stock.roic) if stock.roic else None,
                    'dy': float(stock.div_yield) if stock.div_yield else None,
                    'score_classificacao': float(stock.score_final) if stock.score_final else None,
                    'data_ultima_atualizacao': stock.data_atualizacao.isoformat() if stock.data_atualizacao else None
                }
                
                return jsonify({
                    'success': True,
                    'stock': stock_data
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Ativo {ticker} não encontrado na base de dados'
                })
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar informações do ativo'
        }), 500

@api_bp.route('/stocks/suggestions')
def stock_suggestions():
    """API para sugestões de autocomplete de tickers"""
    query = request.args.get('q', '').upper().strip()
    
    if not query or len(query) < 2:
        return jsonify({'suggestions': []})
    
    try:
        with SessionLocal() as db:
            # Buscar sugestões usando ORM
            # Ordenação simplificada para compatibilidade PostgreSQL
            stocks = db.query(Stock.ticker, Stock.empresa).filter(
                (func.upper(Stock.ticker).like(f'%{query}%')) | 
                (func.upper(Stock.empresa).like(f'%{query}%'))
            ).order_by(Stock.ticker).limit(10).all()
            
            suggestions = [
                {
                    'ticker': row[0],
                    'nome': row[1],
                    'display': f"{row[0]} - {row[1]}"
                }
                for row in stocks
            ]
            
            return jsonify({'suggestions': suggestions})
            
    except Exception as e:
        return jsonify({'suggestions': []}), 500

@api_bp.route('/stocks/<ticker>')
def get_stock_details(ticker):
    """API para obter detalhes completos de uma ação"""
    ticker = ticker.upper().strip()
    
    try:
        with SessionLocal() as db:
            stock = db.query(Stock).filter(
                func.upper(Stock.ticker) == ticker
            ).order_by(Stock.data_atualizacao.desc()).first()
            
            if stock:
                # Converter para dicionário
                stock_data = stock.to_dict()
                
                return jsonify({
                    'success': True,
                    'stock': stock_data
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Ativo {ticker} não encontrado'
                })
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar detalhes do ativo'
        }), 500

@api_bp.route('/market/summary')
def market_summary():
    """API para resumo do mercado"""
    try:
        with SessionLocal() as db:
            # Estatísticas gerais do mercado usando ORM
            result = db.query(
                func.count(Stock.id).label('total_ativos'),
                func.count(Stock.cotacao).label('ativos_com_cotacao'),
                func.avg(Stock.pl).label('avg_pl'),
                func.avg(Stock.div_yield).label('avg_dy'),
                func.avg(Stock.roic).label('avg_roic')
            ).first()
            
            if result:
                summary = {
                    'total_ativos': result.total_ativos or 0,
                    'ativos_com_cotacao': result.ativos_com_cotacao or 0,
                    'avg_pl': float(result.avg_pl) if result.avg_pl else None,
                    'avg_dy': float(result.avg_dy) if result.avg_dy else None,
                    'avg_roic': float(result.avg_roic) if result.avg_roic else None
                }
                
                return jsonify({
                    'success': True,
                    'summary': summary
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Nenhuma informação disponível'
                })
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar resumo do mercado'
        }), 500

# Handler de erro para API
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint não encontrado'
    }), 404

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Erro interno do servidor'
    }), 500