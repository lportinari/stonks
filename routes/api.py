from flask import Blueprint, jsonify, request
from typing import Dict, List, Optional
import logging
from services.ranking_service import RankingService
from services.cache_manager import CacheManager, CacheKeys

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

ranking_service = RankingService()
cache_manager = CacheManager()

@api_bp.route('/ranking')
def get_ranking():
    """API para obter ranking de ações"""
    try:
        # Parâmetros
        limit = request.args.get('limit', 50, type=int)
        sector = request.args.get('sector')
        page = request.args.get('page', 1, type=int)
        
        # Validar limit
        if limit > 200:
            limit = 200
        
        # Obter dados
        if sector:
            stocks = ranking_service.get_sector_ranking(sector, limit)
        else:
            stocks = ranking_service.get_current_ranking(limit)
        
        # Converter para JSON
        data = {
            'success': True,
            'data': [stock.to_dict() for stock in stocks],
            'count': len(stocks),
            'page': page,
            'sector_filter': sector
        }
        
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Erro na API de ranking: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/stock/<ticker>')
def get_stock(ticker):
    """API para obter dados de uma ação específica"""
    try:
        stock = ranking_service.get_stock_by_ticker(ticker.upper())
        
        if not stock:
            return jsonify({
                'success': False,
                'error': f'Ação {ticker} não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'data': stock.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Erro na API de detalhes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/compare')
def compare_stocks():
    """API para comparar múltiplas ações"""
    try:
        tickers = request.args.get('tickers', '').split(',')
        tickers = [t.strip().upper() for t in tickers if t.strip()]
        
        if len(tickers) < 2:
            return jsonify({
                'success': False,
                'error': 'Informe pelo menos 2 tickers'
            }), 400
        
        if len(tickers) > 10:
            return jsonify({
                'success': False,
                'error': 'Máximo de 10 ações por comparação'
            }), 400
        
        comparison_data = ranking_service.compare_stocks(tickers)
        
        return jsonify({
            'success': True,
            'data': comparison_data,
            'count': len(comparison_data)
        })
    
    except Exception as e:
        logger.error(f"Erro na API de comparação: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sectors')
def get_sectors():
    """API para obter lista de setores disponíveis"""
    try:
        sectors = ranking_service.get_available_sectors()
        
        return jsonify({
            'success': True,
            'data': sectors,
            'count': len(sectors)
        })
    
    except Exception as e:
        logger.error(f"Erro na API de setores: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/filter')
def filter_stocks():
    """API para filtrar ações com critérios avançados"""
    try:
        # Parâmetros de filtro
        min_dy = request.args.get('min_dy', type=float)
        max_pl = request.args.get('max_pl', type=float)
        max_pvp = request.args.get('max_pvp', type=float)
        min_roe = request.args.get('min_roe', type=float)
        sector = request.args.get('sector')
        limit = request.args.get('limit', 100, type=int)
        
        # Validar limit
        if limit > 500:
            limit = 500
        
        # Aplicar filtros
        filtered_stocks = ranking_service.filter_stocks(
            min_dy=min_dy,
            max_pl=max_pl,
            max_pvp=max_pvp,
            min_roe=min_roe,
            sector=sector,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': [stock.to_dict() for stock in filtered_stocks],
            'count': len(filtered_stocks),
            'filters': {
                'min_dy': min_dy,
                'max_pl': max_pl,
                'max_pvp': max_pvp,
                'min_roe': min_roe,
                'sector': sector
            }
        })
    
    except Exception as e:
        logger.error(f"Erro na API de filtros: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/stats')
def get_statistics():
    """API para obter estatísticas do ranking"""
    try:
        stats = ranking_service.get_ranking_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        logger.error(f"Erro na API de estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/top')
def get_top_stocks():
    """API para obter as top N ações"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Validar limit
        if limit < 1 or limit > 50:
            limit = 10
        
        top_stocks = ranking_service.get_top_stocks(limit)
        
        return jsonify({
            'success': True,
            'data': [stock.to_dict() for stock in top_stocks],
            'count': len(top_stocks)
        })
    
    except Exception as e:
        logger.error(f"Erro na API de top stocks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/search')
def search_stocks():
    """API para buscar ações por nome ou ticker"""
    try:
        query = request.args.get('q', '').strip().upper()
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query de busca não informada'
            }), 400
        
        # Buscar ações (implementação básica - pode ser melhorada)
        all_stocks = ranking_service.get_current_ranking(limit=500)
        
        # Filtrar por ticker ou nome da empresa
        filtered_stocks = []
        for stock in all_stocks:
            if (query in stock.ticker.upper() or 
                query in stock.empresa.upper()):
                filtered_stocks.append(stock)
            
            if len(filtered_stocks) >= limit:
                break
        
        return jsonify({
            'success': True,
            'data': [stock.to_dict() for stock in filtered_stocks],
            'count': len(filtered_stocks),
            'query': query
        })
    
    except Exception as e:
        logger.error(f"Erro na API de busca: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """API para limpar cache (admin)"""
    try:
        # TODO: Adicionar autenticação/admin
        cache_manager.clear_all()
        
        return jsonify({
            'success': True,
            'message': 'Cache limpo com sucesso'
        })
    
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/cache/info')
def get_cache_info():
    """API para obter informações do cache"""
    try:
        cache_info = cache_manager.get_cache_info()
        
        return jsonify({
            'success': True,
            'data': cache_info
        })
    
    except Exception as e:
        logger.error(f"Erro ao obter info do cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/config/weights')
def get_weights():
    """API para obter pesos atuais"""
    try:
        from config import Config
        
        return jsonify({
            'success': True,
            'data': Config.DEFAULT_WEIGHTS
        })
    
    except Exception as e:
        logger.error(f"Erro ao obter pesos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/config/weights', methods=['POST'])
def update_weights():
    """API para atualizar pesos do ranking"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        # Validar pesos
        required_fields = ['dy', 'pl', 'pvp', 'roe', 'margem_liquida']
        weights = {}
        total_weight = 0
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} não informado'
                }), 400
            
            weight = float(data[field])
            if weight < 0:
                return jsonify({
                    'success': False,
                    'error': f'Peso {field} não pode ser negativo'
                }), 400
            
            weights[field] = weight
            total_weight += weight
        
        # Validar soma
        if abs(total_weight - 1.0) > 0.01:
            return jsonify({
                'success': False,
                'error': f'A soma dos pesos deve ser 1.0. Soma atual: {total_weight}'
            }), 400
        
        # Atualizar ranking
        updated_count = ranking_service.update_ranking(weights)
        
        # Limpar cache
        cache_manager.invalidate(CacheKeys.RANKING_DATA)
        cache_manager.invalidate(CacheKeys.TOP_STOCKS)
        
        return jsonify({
            'success': True,
            'message': f'Pesos atualizados! {updated_count} ações reprocessadas.',
            'data': {
                'weights': weights,
                'updated_count': updated_count
            }
        })
    
    except Exception as e:
        logger.error(f"Erro ao atualizar pesos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Tratamento de erros globais da API
@api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Requisição inválida'
    }), 400

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Recurso não encontrado'
    }), 404

@api_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno na API: {error}")
    return jsonify({
        'success': False,
        'error': 'Erro interno do servidor'
    }), 500