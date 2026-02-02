import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from models.purchase import Purchase, create_purchase, get_purchases_by_user, get_purchase_by_id, update_purchase, delete_purchase, get_portfolio_summary, get_portfolio_distribution, get_portfolio_performance

logger = logging.getLogger(__name__)

class PurchaseService:
    """Serviço responsável pela gestão de compras de ativos"""
    
    def criar_compra(self, user_id: int, ticker: str, nome_ativo: str, 
                    quantidade: int, preco_unitario: float, taxas: float = 0.0, 
                    data_compra: date = None) -> Dict[str, Any]:
        """Cria uma nova compra de ativo"""
        try:
            # Validações básicas
            if not ticker or len(ticker) > 10:
                return {'success': False, 'message': 'Ticker inválido'}
            
            if not nome_ativo or len(nome_ativo) < 2:
                return {'success': False, 'message': 'Nome do ativo inválido'}
            
            if quantidade <= 0:
                return {'success': False, 'message': 'Quantidade deve ser maior que zero'}
            
            if preco_unitario <= 0:
                return {'success': False, 'message': 'Preço unitário deve ser maior que zero'}
            
            if taxas < 0:
                return {'success': False, 'message': 'Taxas não podem ser negativas'}
            
            # Criar compra
            purchase_id = create_purchase(
                user_id=user_id,
                ticker=ticker.upper().strip(),
                nome_ativo=nome_ativo.strip(),
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                taxas=taxas,
                data_compra=data_compra
            )
            
            if purchase_id:
                logger.info(f"Compra criada: ID {purchase_id}, User {user_id}, {ticker}")
                return {
                    'success': True,
                    'message': 'Compra registrada com sucesso!',
                    'purchase_id': purchase_id
                }
            else:
                return {'success': False, 'message': 'Erro ao registrar compra'}
                
        except Exception as e:
            logger.error(f"Erro ao criar compra: {e}")
            return {'success': False, 'message': f'Erro ao criar compra: {str(e)}'}
    
    def listar_compras(self, user_id: int, page: int = 1, per_page: int = 20, 
                      order_by: str = 'data_compra', order_dir: str = 'DESC',
                      ticker_filter: str = None) -> Dict[str, Any]:
        """Lista compras do usuário com paginação e filtros"""
        try:
            offset = (page - 1) * per_page
            
            # Buscar compras
            compras = get_purchases_by_user(
                user_id=user_id,
                limit=per_page,
                offset=offset,
                order_by=order_by,
                order_dir=order_dir
            )
            
            # Aplicar filtro por ticker se especificado
            if ticker_filter:
                compras = [c for c in compras if c.ticker.upper() == ticker_filter.upper()]
            
            # Converter para dicionários
            compras_data = [compra.to_dict() for compra in compras]
            
            # Buscar total para paginação
            total_compras = self._get_total_compras(user_id, ticker_filter)
            total_pages = (total_compras + per_page - 1) // per_page if total_compras > 0 else 0
            
            return {
                'success': True,
                'compras': compras_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_compras,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar compras: {e}")
            return {'success': False, 'message': f'Erro ao listar compras: {str(e)}'}
    
    def obter_compra(self, purchase_id: int, user_id: int) -> Dict[str, Any]:
        """Obtém uma compra específica"""
        try:
            compra = get_purchase_by_id(purchase_id, user_id)
            
            if compra:
                return {
                    'success': True,
                    'compra': compra.to_dict()
                }
            else:
                return {'success': False, 'message': 'Compra não encontrada'}
                
        except Exception as e:
            logger.error(f"Erro ao obter compra: {e}")
            return {'success': False, 'message': f'Erro ao obter compra: {str(e)}'}
    
    def atualizar_compra(self, purchase_id: int, user_id: int, **kwargs) -> Dict[str, Any]:
        """Atualiza dados de uma compra"""
        try:
            # Validações
            allowed_fields = ['ticker', 'nome_ativo', 'quantidade', 'preco_unitario', 'taxas', 'data_compra']
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == 'ticker' and (not value or len(value) > 10):
                        return {'success': False, 'message': 'Ticker inválido'}
                    elif field == 'nome_ativo' and (not value or len(value) < 2):
                        return {'success': False, 'message': 'Nome do ativo inválido'}
                    elif field == 'quantidade' and value <= 0:
                        return {'success': False, 'message': 'Quantidade deve ser maior que zero'}
                    elif field == 'preco_unitario' and value <= 0:
                        return {'success': False, 'message': 'Preço unitário deve ser maior que zero'}
                    elif field == 'taxas' and value < 0:
                        return {'success': False, 'message': 'Taxas não podem ser negativas'}
            
            # Atualizar compra
            success = update_purchase(purchase_id, user_id, **kwargs)
            
            if success:
                logger.info(f"Compra atualizada: ID {purchase_id}, User {user_id}")
                return {
                    'success': True,
                    'message': 'Compra atualizada com sucesso!'
                }
            else:
                return {'success': False, 'message': 'Compra não encontrada ou sem alterações'}
                
        except Exception as e:
            logger.error(f"Erro ao atualizar compra: {e}")
            return {'success': False, 'message': f'Erro ao atualizar compra: {str(e)}'}
    
    def excluir_compra(self, purchase_id: int, user_id: int) -> Dict[str, Any]:
        """Exclui uma compra"""
        try:
            success = delete_purchase(purchase_id, user_id)
            
            if success:
                logger.info(f"Compra excluída: ID {purchase_id}, User {user_id}")
                return {
                    'success': True,
                    'message': 'Compra excluída com sucesso!'
                }
            else:
                return {'success': False, 'message': 'Compra não encontrada'}
                
        except Exception as e:
            logger.error(f"Erro ao excluir compra: {e}")
            return {'success': False, 'message': f'Erro ao excluir compra: {str(e)}'}
    
    def get_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Obtém dados para o dashboard"""
        try:
            # Resumo do portfolio
            summary = get_portfolio_summary(user_id)
            
            # Distribuição por ativo
            distribution = get_portfolio_distribution(user_id)
            
            # Performance dos ativos
            performance = get_portfolio_performance(user_id)
            
            # Compras recentes
            compras_recentes = get_purchases_by_user(
                user_id=user_id,
                limit=5,
                order_by='data_compra',
                order_dir='DESC'
            )
            
            # Construir portfolio completo
            portfolio_data = {
                'total_investido': summary.get('total_investido', 0) if summary else 0,
                'valor_atual': performance.get('resumo', {}).get('valor_atual_total', 0) if performance else 0,
                'resultado_total': performance.get('resumo', {}).get('resultado_total', 0) if performance else 0,
                'rentabilidade_total': performance.get('resumo', {}).get('resultado_percentual_total', 0) if performance else 0,
                'posicoes': performance.get('tickers', []) if performance else [],
                'analise_setor': {}
            }
            
            return {
                'success': True,
                'resumo': portfolio_data,
                'distribuicao': [dict(row) for row in distribution] if distribution else [],
                'performance': performance,
                'compras_recentes': [compra.to_dict() for compra in compras_recentes]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados do dashboard: {e}")
            return {'success': False, 'message': f'Erro ao carregar dashboard: {str(e)}'}
    
    def get_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        """Obtém resumo do portfolio"""
        try:
            return get_portfolio_summary(user_id)
        except Exception as e:
            logger.error(f"Erro ao obter resumo do portfolio: {e}")
            return {}
    
    def get_tickers_usuario(self, user_id: int) -> List[str]:
        """Obtém lista de tickers do usuário"""
        try:
            with sqlite3.connect('database/stocks.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT ticker FROM purchases 
                    WHERE user_id = ? 
                    ORDER BY ticker
                ''', (user_id,))
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Erro ao obter tickers: {e}")
            return []
    
    def _get_total_compras(self, user_id: int, ticker_filter: str = None) -> int:
        """Obtém total de compras para paginação"""
        try:
            with sqlite3.connect('database/stocks.db') as conn:
                cursor = conn.cursor()
                if ticker_filter:
                    cursor.execute('''
                        SELECT COUNT(*) FROM purchases 
                        WHERE user_id = ? AND UPPER(ticker) = ?
                    ''', (user_id, ticker_filter.upper()))
                else:
                    cursor.execute('SELECT COUNT(*) FROM purchases WHERE user_id = ?', (user_id,))
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Erro ao contar compras: {e}")
            return 0
    
    def search_compras(self, user_id: int, query: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Busca compras por texto"""
        try:
            offset = (page - 1) * per_page
            
            with sqlite3.connect('database/stocks.db') as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                search_pattern = f'%{query.upper()}%'
                cursor.execute('''
                    SELECT * FROM purchases 
                    WHERE user_id = ? 
                    AND (UPPER(ticker) LIKE ? OR UPPER(nome_ativo) LIKE ?)
                    ORDER BY data_compra DESC
                    LIMIT ? OFFSET ?
                ''', (user_id, search_pattern, search_pattern, per_page, offset))
                
                rows = cursor.fetchall()
                
                compras = []
                for row in rows:
                    compra = Purchase(
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
                        criado_em=datetime.fromisoformat(row['criado_em']) if row['criado_em'] else None,
                        atualizado_em=datetime.fromisoformat(row['atualizado_em']) if row['atualizado_em'] else None
                    )
                    compras.append(compra)
                
                # Buscar total
                cursor.execute('''
                    SELECT COUNT(*) FROM purchases 
                    WHERE user_id = ? 
                    AND (UPPER(ticker) LIKE ? OR UPPER(nome_ativo) LIKE ?)
                ''', (user_id, search_pattern, search_pattern))
                total_compras = cursor.fetchone()[0]
                
                total_pages = (total_compras + per_page - 1) // per_page
                
                return {
                    'success': True,
                    'compras': [compra.to_dict() for compra in compras],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total_compras,
                        'total_pages': total_pages,
                        'has_prev': page > 1,
                        'has_next': page < total_pages
                    },
                    'query': query
                }
                
        except Exception as e:
            logger.error(f"Erro na busca de compras: {e}")
            return {'success': False, 'message': f'Erro na busca: {str(e)}'}