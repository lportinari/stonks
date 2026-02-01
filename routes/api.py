from flask import Blueprint, jsonify, request
from models.stock import Stock
from models.database import get_db

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/stocks/search')
def search_stocks():
    """API para buscar ações por ticker"""
    ticker = request.args.get('ticker', '').upper().strip()
    
    if not ticker or len(ticker) < 3:
        return jsonify({'success': False, 'message': 'Ticker inválido'})
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Buscar ação no banco
            cursor.execute('''
                SELECT ticker, nome, setor, papel, 
                       cotacao, pl, lpa, vpa, roe, roic, 
                       dy, p_vp, p_ebit, ev_ebit, 
                       marg_liquida, marg_ebit, ebitda, 
                       div_liq, patrimonio_liquido, dl_patr_pl,
                       score_classificacao, data_ultima_atualizacao
                FROM stocks 
                WHERE UPPER(ticker) = ?
                ORDER BY data_ultima_atualizacao DESC
                LIMIT 1
            ''', (ticker,))
            
            result = cursor.fetchone()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                stock = dict(zip(columns, result))
                
                # Formatar dados para resposta
                stock_data = {
                    'ticker': stock['ticker'],
                    'nome': stock['nome'],
                    'setor': stock['setor'],
                    'papel': stock['papel'],
                    'cotacao': float(stock['cotacao']) if stock['cotacao'] else None,
                    'pl': float(stock['pl']) if stock['pl'] else None,
                    'roic': float(stock['roic']) if stock['roic'] else None,
                    'dy': float(stock['dy']) if stock['dy'] else None,
                    'score_classificacao': stock['score_classificacao'],
                    'data_ultima_atualizacao': stock['data_ultima_atualizacao']
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
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Buscar sugestões (limitar a 10 resultados)
            cursor.execute('''
                SELECT DISTINCT ticker, nome
                FROM stocks 
                WHERE UPPER(ticker) LIKE ? OR UPPER(nome) LIKE ?
                ORDER BY 
                    CASE WHEN UPPER(ticker) = ? THEN 1
                         WHEN UPPER(ticker) LIKE ? THEN 2
                         ELSE 3
                    END,
                    ticker
                LIMIT 10
            ''', (f'%{query}%', f'%{query}%', query, f'{query}%'))
            
            results = cursor.fetchall()
            
            suggestions = [
                {
                    'ticker': row[0],
                    'nome': row[1],
                    'display': f"{row[0]} - {row[1]}"
                }
                for row in results
            ]
            
            return jsonify({'suggestions': suggestions})
            
    except Exception as e:
        return jsonify({'suggestions': []}), 500

@api_bp.route('/stocks/<ticker>')
def get_stock_details(ticker):
    """API para obter detalhes completos de uma ação"""
    ticker = ticker.upper().strip()
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM stocks 
                WHERE UPPER(ticker) = ?
                ORDER BY data_ultima_atualizacao DESC
                LIMIT 1
            ''', (ticker,))
            
            result = cursor.fetchone()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                stock = dict(zip(columns, result))
                
                # Converter para tipos JSON serializáveis
                for key, value in stock.items():
                    if value is None:
                        continue
                    elif isinstance(value, (int, float)):
                        stock[key] = float(value)
                    else:
                        stock[key] = str(value)
                
                return jsonify({
                    'success': True,
                    'stock': stock
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
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Estatísticas gerais do mercado
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_ativos,
                    COUNT(CASE WHEN cotacao IS NOT NULL THEN 1 END) as ativos_com_cotacao,
                    AVG(CASE WHEN pl IS NOT NULL AND pl > 0 THEN pl END) as avg_pl,
                    AVG(CASE WHEN dy IS NOT NULL AND dy > 0 THEN dy END) as avg_dy,
                    AVG(CASE WHEN roic IS NOT NULL AND roic > 0 THEN roic END) as avg_roic
                FROM stocks
            ''')
            
            result = cursor.fetchone()
            
            if result:
                summary = {
                    'total_ativos': result[0],
                    'ativos_com_cotacao': result[1],
                    'avg_pl': float(result[2]) if result[2] else None,
                    'avg_dy': float(result[3]) if result[3] else None,
                    'avg_roic': float(result[4]) if result[4] else None
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