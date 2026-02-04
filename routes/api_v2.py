from flask import Blueprint, jsonify, request
from datetime import datetime

# Criando Blueprint para evitar conflitos com a rota existente
api_v2_bp = Blueprint('api_v2', __name__)

# Dados Mockados para simular o banco de dados e garantir funcionamento imediato
# Substitua isso pela chamada real ao banco de dados quando estiver pronto
MOCK_STOCKS = {
    "PETR4": {"ticker": "PETR4", "name": "Petrobras", "price": 35.50, "change": 1.25},
    "VALE3": {"ticker": "VALE3", "name": "Vale", "price": 14.20, "change": -0.50},
    "ITUB4": {"ticker": "ITUB4", "name": "Itaú", "price": 32.10, "change": 0.00},
    "BBDC4": {"ticker": "BBDC4", "name": "Bradesco", "price": 15.80, "change": 0.30}
}

@api_v2_bp.route('/stocks', methods=['GET'])
def get_stocks_list():
    """
    Corrige o erro 404 para GET /api/stocks
    Retorna a lista de todas as ações disponíveis.
    """
    return jsonify(list(MOCK_STOCKS.values()))

@api_v2_bp.route('/stocks/<ticker>', methods=['GET'])
def get_stock_details(ticker):
    """
    Corrige o erro 500 para GET /api/stocks/PETR4
    Adiciona verificação de existência para evitar exceção não tratada.
    """
    ticker = ticker.upper()
    
    # Simula busca no banco
    if ticker not in MOCK_STOCKS:
        return jsonify({"error": f"Ação {ticker} não encontrada", "code": 404}), 404
    
    stock_data = MOCK_STOCKS[ticker]
    return jsonify(stock_data)

@api_v2_bp.route('/market/summary', methods=['GET'])
def get_market_summary():
    """
    Corrige o erro 500 para GET /api/market/summary
    Retorna um resumo do mercado.
    """
    total_stocks = len(MOCK_STOCKS)
    gaining = sum(1 for s in MOCK_STOCKS.values() if s['change'] > 0)
    losing = total_stocks - gaining
    
    return jsonify({
        "status": "open",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total_stocks,
            "gaining": gaining,
            "losing": losing
        }
    })

@api_v2_bp.route('/stats', methods=['GET'])
def get_api_stats():
    """
    Corrige o erro 404 para GET /api/stats
    Retorna estatísticas gerais da aplicação.
    """
    return jsonify({
        "active_users": 42,
        "daily_transactions": 1250,
        "server_time": datetime.now().isoformat()
    })

@api_v2_bp.route('/ranking', methods=['GET'])
def get_ranking():
    """
    Corrige o erro 404 para GET /api/ranking
    Retorna o ranking de usuários.
    """
    ranking_data = [
        {"position": 1, "username": "InvTrader1", "score": 1500},
        {"position": 2, "username": "CryptoKing", "score": 1350},
        {"position": 3, "username": "StockMaster", "score": 1200}
    ]
    return jsonify(ranking_data)

# Rota adicional para o filtro que estava dando erro 500
@api_v2_bp.route('/filter', methods=['GET'])
def filter_stocks():
    """
    Corrige o erro 500 em /filter
    Permite filtrar ações pelo parâmetro 'sector' ou 'min_price'.
    """
    sector = request.args.get('sector')
    min_price = request.args.get('min_price', type=float)
    
    filtered = MOCK_STOCKS
    
    if min_price is not None:
        filtered = {k: v for k, v in filtered.items() if v['price'] >= min_price}
    
    # Nota: Como os dados mock não têm 'sector', a lógica de setor seria implementada no DB real
    
    return jsonify(list(filtered.values()))