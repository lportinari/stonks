import sqlite3
from datetime import datetime, date

class Purchase:
    """Modelo de Compra para SQLite"""
    
    def __init__(self, id=None, user_id=None, ticker=None, nome_ativo=None, 
                 quantidade=None, preco_unitario=None, taxas=0.0, custo_total=None,
                 preco_medio=None, data_compra=None, quantidade_vendida=0,
                 preco_venda=None, data_venda=None, classe_ativo=None,
                 criado_em=None, atualizado_em=None):
        self.id = id
        self.user_id = user_id
        self.ticker = ticker
        self.nome_ativo = nome_ativo
        self.quantidade = quantidade
        self.preco_unitario = preco_unitario
        self.taxas = taxas
        self.custo_total = custo_total
        self.preco_medio = preco_medio
        self.data_compra = data_compra
        self.quantidade_vendida = quantidade_vendida
        self.preco_venda = preco_venda
        self.data_venda = data_venda
        self.classe_ativo = classe_ativo
        self.criado_em = criado_em
        self.atualizado_em = atualizado_em
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ticker': self.ticker,
            'nome_ativo': self.nome_ativo,
            'quantidade': self.quantidade,
            'preco_unitario': self.preco_unitario,
            'taxas': self.taxas,
            'custo_total': self.custo_total,
            'preco_medio': self.preco_medio,
            'data_compra': self.data_compra.isoformat() if self.data_compra else None,
            'quantidade_vendida': self.quantidade_vendida,
            'preco_venda': self.preco_venda,
            'data_venda': self.data_venda.isoformat() if self.data_venda else None,
            'classe_ativo': self.classe_ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
    
    def __repr__(self):
        return f'<Purchase {self.ticker} - {self.quantidade} unidades>'

def create_purchase(user_id, ticker, nome_ativo, quantidade, preco_unitario, taxas=0.0, data_compra=None, classe_ativo=None):
    """Cria uma nova compra"""
    if data_compra is None:
        data_compra = date.today()
    
    # Calcular custo total e preço médio
    quantidade = int(quantidade)
    preco_unitario = float(preco_unitario)
    taxas = float(taxas)
    custo_total = (quantidade * preco_unitario) + taxas
    preco_medio = custo_total / quantidade
    
    with sqlite3.connect('database/stocks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO purchases (user_id, ticker, nome_ativo, quantidade, preco_unitario, 
                                 taxas, custo_total, preco_medio, data_compra, classe_ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, ticker, nome_ativo, quantidade, preco_unitario, 
               taxas, custo_total, preco_medio, data_compra, classe_ativo))
        conn.commit()
        return cursor.lastrowid

def get_purchases_by_user(user_id, limit=50, offset=0, order_by='data_compra', order_dir='DESC'):
    """Busca compras de um usuário com paginação"""
    with sqlite3.connect('database/stocks.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        order_clause = f"ORDER BY {order_by} {order_dir}"
        
        cursor.execute(f'''
            SELECT * FROM purchases 
            WHERE user_id = ? 
            {order_clause}
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        
        rows = cursor.fetchall()
        
        purchases = []
        for row in rows:
            purchase = Purchase(
                id=row['id'],
                user_id=row['user_id'],
                ticker=row['ticker'],
                nome_ativo=row['nome_ativo'],
                quantidade=row['quantidade'],
                preco_unitario=row['preco_unitario'],
                taxas=row['taxas'],
                custo_total=row['custo_total'],
                preco_medio=row['preco_medio'],
                data_compra=datetime.strptime(row['data_compra'], '%Y-%m-%d').date(),
                quantidade_vendida=row['quantidade_vendida'],
                preco_venda=row['preco_venda'],
                data_venda=datetime.strptime(row['data_venda'], '%Y-%m-%d').date() if row['data_venda'] else None,
                classe_ativo=row['classe_ativo'] if 'classe_ativo' in row.keys() else None,
                criado_em=datetime.fromisoformat(row['criado_em']) if row['criado_em'] else None,
                atualizado_em=datetime.fromisoformat(row['atualizado_em']) if row['atualizado_em'] else None
            )
            purchases.append(purchase)
        
        return purchases

def get_purchase_by_id(purchase_id, user_id):
    """Busca uma compra específica do usuário"""
    with sqlite3.connect('database/stocks.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM purchases WHERE id = ? AND user_id = ?', (purchase_id, user_id))
        row = cursor.fetchone()
        
        if row:
            return Purchase(
                id=row['id'],
                user_id=row['user_id'],
                ticker=row['ticker'],
                nome_ativo=row['nome_ativo'],
                quantidade=row['quantidade'],
                preco_unitario=row['preco_unitario'],
                taxas=row['taxas'],
                custo_total=row['custo_total'],
                preco_medio=row['preco_medio'],
                data_compra=datetime.strptime(row['data_compra'], '%Y-%m-%d').date(),
                quantidade_vendida=row['quantidade_vendida'],
                preco_venda=row['preco_venda'],
                data_venda=datetime.strptime(row['data_venda'], '%Y-%m-%d').date() if row['data_venda'] else None,
                classe_ativo=row.get('classe_ativo'),
                criado_em=datetime.fromisoformat(row['criado_em']) if row['criado_em'] else None,
                atualizado_em=datetime.fromisoformat(row['atualizado_em']) if row['atualizado_em'] else None
            )
        return None

def update_purchase(purchase_id, user_id, **kwargs):
    """Atualiza uma compra"""
    allowed_fields = ['ticker', 'nome_ativo', 'quantidade', 'preco_unitario', 'taxas', 'data_compra']
    
    set_clause = []
    values = []
    
    for field, value in kwargs.items():
        if field in allowed_fields:
            set_clause.append(f"{field} = ?")
            values.append(value)
    
    if not set_clause:
        return False
    
    values.append(purchase_id)
    values.append(user_id)
    
    with sqlite3.connect('database/stocks.db') as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE purchases 
            SET {', '.join(set_clause)}, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', values)
        conn.commit()
        return cursor.rowcount > 0

def delete_purchase(purchase_id, user_id):
    """Deleta uma compra"""
    with sqlite3.connect('database/stocks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM purchases WHERE id = ? AND user_id = ?', (purchase_id, user_id))
        conn.commit()
        return cursor.rowcount > 0

def get_portfolio_summary(user_id):
    """Resume o portfolio do usuário"""
    try:
        with sqlite3.connect('database/stocks.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_compras,
                    COALESCE(SUM(custo_total), 0) as total_investido,
                    COALESCE(SUM(quantidade), 0) as total_ativos,
                    COUNT(DISTINCT ticker) as total_tickers,
                    COALESCE(AVG(preco_medio), 0) as preco_medio_geral
                FROM purchases 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            # Converter Row para dict para evitar erros
            if result:
                return {
                    'total_compras': result['total_compras'] or 0,
                    'total_investido': result['total_investido'] or 0,
                    'total_ativos': result['total_ativos'] or 0,
                    'total_tickers': result['total_tickers'] or 0,
                    'preco_medio_geral': result['preco_medio_geral'] or 0
                }
            
            return {
                'total_compras': 0,
                'total_investido': 0,
                'total_ativos': 0,
                'total_tickers': 0,
                'preco_medio_geral': 0
            }
            
    except Exception as e:
        print(f"Erro ao obter resumo do portfolio: {e}")
        return {
            'total_compras': 0,
            'total_investido': 0,
            'total_ativos': 0,
            'total_tickers': 0,
            'preco_medio_geral': 0
        }

def get_purchases_by_ticker(user_id, ticker):
    """Busca compras de um ticker específico"""
    with sqlite3.connect('database/stocks.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM purchases 
            WHERE user_id = ? AND ticker = ?
            ORDER BY data_compra ASC
        ''', (user_id, ticker))
        
        rows = cursor.fetchall()
        
        purchases = []
        for row in rows:
            purchase = Purchase(
                id=row['id'],
                user_id=row['user_id'],
                ticker=row['ticker'],
                nome_ativo=row['nome_ativo'],
                quantidade=row['quantidade'],
                preco_unitario=row['preco_unitario'],
                taxas=row['taxas'],
                custo_total=row['custo_total'],
                preco_medio=row['preco_medio'],
                data_compra=datetime.strptime(row['data_compra'], '%Y-%m-%d').date(),
                quantidade_vendida=row['quantidade_vendida'],
                preco_venda=row['preco_venda'],
                data_venda=datetime.strptime(row['data_venda'], '%Y-%m-%d').date() if row['data_venda'] else None,
                classe_ativo=row.get('classe_ativo'),
                criado_em=datetime.fromisoformat(row['criado_em']) if row['criado_em'] else None,
                atualizado_em=datetime.fromisoformat(row['atualizado_em']) if row['atualizado_em'] else None
            )
            purchases.append(purchase)
        
        return purchases

def get_portfolio_distribution(user_id):
    """Busca distribuição do portfolio por ticker"""
    try:
        with sqlite3.connect('database/stocks.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    ticker,
                    nome_ativo,
                    COALESCE(SUM(quantidade), 0) as total_quantidade,
                    COALESCE(SUM(custo_total), 0) as total_custo,
                    COALESCE(AVG(preco_medio), 0) as preco_medio,
                    COUNT(*) as num_compras
                FROM purchases 
                WHERE user_id = ?
                GROUP BY ticker, nome_ativo
                ORDER BY total_custo DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            
            # Converter Row objects para dicts
            return [dict(row) for row in rows]
            
    except Exception as e:
        print(f"Erro ao obter distribuição do portfolio: {e}")
        return []

def get_portfolio_performance(user_id):
    """Calcula performance do portfolio"""
    with sqlite3.connect('database/stocks.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar dados agrupados por ticker
        cursor.execute('''
            SELECT 
                ticker,
                nome_ativo,
                SUM(quantidade) as total_quantidade,
                SUM(custo_total) as total_custo,
                AVG(preco_medio) as preco_medio_calculado
            FROM purchases 
            WHERE user_id = ?
            GROUP BY ticker, nome_ativo
            ORDER BY total_custo DESC
        ''', (user_id,))
        
        tickers_data = cursor.fetchall()
        
        performance_data = []
        total_investido = 0
        
        for ticker_info in tickers_data:
            ticker = ticker_info['ticker']
            quantidade = ticker_info['total_quantidade']
            custo_total = ticker_info['total_custo']
            preco_medio_calculado = ticker_info['preco_medio_calculado']
            
            total_investido += custo_total
            
            # Simular preço atual (em produção, buscar de API)
            preco_atual = preco_medio_calculado * (1 + (hash(ticker) % 20 - 10) / 100)  # Variação -10% a +10%
            valor_atual = quantidade * preco_atual
            resultado = valor_atual - custo_total
            resultado_percentual = (resultado / custo_total) * 100 if custo_total > 0 else 0
            
            performance_data.append({
                'ticker': ticker,
                'nome_ativo': ticker_info['nome_ativo'],
                'quantidade': quantidade,
                'custo_total': custo_total,
                'preco_medio': preco_medio_calculado,
                'preco_atual': preco_atual,
                'valor_atual': valor_atual,
                'resultado': resultado,
                'resultado_percentual': resultado_percentual
            })
        
        # Calcular totais
        valor_atual_total = sum(item['valor_atual'] for item in performance_data)
        resultado_total = valor_atual_total - total_investido
        resultado_percentual_total = (resultado_total / total_investido) * 100 if total_investido > 0 else 0
        
        return {
            'tickers': performance_data,
            'resumo': {
                'total_investido': total_investido,
                'valor_atual_total': valor_atual_total,
                'resultado_total': resultado_total,
                'resultado_percentual_total': resultado_percentual_total
            }
        }