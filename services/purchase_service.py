import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from models.purchase import Purchase, create_purchase, get_purchases_by_user, get_purchase_by_id, update_purchase, delete_purchase, get_portfolio_summary, get_portfolio_distribution, get_portfolio_performance, get_portfolio_distribution_by_asset_class
from models.database import SessionLocal
from sqlalchemy import func

logger = logging.getLogger(__name__)

class PurchaseService:
    """Serviço responsável pela gestão de compras de ativos"""
    
    def criar_compra(self, user_id: int, ticker: str, nome_ativo: str, 
                    quantidade: float, preco_unitario: float, taxas: float = 0.0, 
                    data_compra: date = None, classe_ativo: str = None) -> Dict[str, Any]:
        """Cria uma nova compra de ativo"""
        try:
            # Validações básicas
            if not ticker or len(ticker) > 50:
                return {'success': False, 'message': 'Ticker inválido'}
            
            if not nome_ativo or len(nome_ativo) < 2:
                return {'success': False, 'message': 'Nome do ativo inválido'}
            
            if quantidade <= 0:
                return {'success': False, 'message': 'Quantidade deve ser maior que zero'}
            
            if preco_unitario <= 0:
                return {'success': False, 'message': 'Preço unitário deve ser maior que zero'}
            
            if taxas < 0:
                return {'success': False, 'message': 'Taxas não podem ser negativas'}
            
            # Validação de classe de ativo
            classes_validas = [
                'acoes',
                'renda_fixa_pos',
                'renda_fixa_dinamica',
                'fundos_imobiliarios',
                'internacional',
                'fundos_multimercados',
                'alternativos'
            ]
            
            if classe_ativo and classe_ativo not in classes_validas:
                return {'success': False, 'message': 'Classe de ativo inválida'}
            
            # Criar compra
            purchase_id = create_purchase(
                user_id=user_id,
                ticker=ticker.upper().strip(),
                nome_ativo=nome_ativo.strip(),
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                taxas=taxas,
                data_compra=data_compra,
                classe_ativo=classe_ativo
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
                    if field == 'ticker' and (not value or len(value) > 50):
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
            
            # Distribuição por classe de ativo
            distrib_classe = get_portfolio_distribution_by_asset_class(user_id)
            
            # Construir portfolio completo
            portfolio_data = {
                'total_investido': summary.get('total_investido', 0) if summary else 0,
                'valor_atual': performance.get('resumo', {}).get('valor_atual_total', 0) if performance else 0,
                'resultado_total': performance.get('resumo', {}).get('resultado_total', 0) if performance else 0,
                'rentabilidade_total': performance.get('resumo', {}).get('resultado_percentual_total', 0) if performance else 0,
                'posicoes': performance.get('tickers', []) if performance else [],
                'analise_setor': {},
                'analise_classe_ativo': distrib_classe.get('distribution', []) if distrib_classe else []
            }
            
            return {
                'success': True,
                'resumo': portfolio_data,
                'distribuicao': [dict(row) for row in distribution] if distribution else [],
                'performance': performance,
                'compras_recentes': [compra.to_dict() for compra in compras_recentes],
                'distrib_classe': distrib_classe
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
            with SessionLocal() as db:
                tickers = db.query(Purchase.ticker).filter(
                    Purchase.user_id == user_id
                ).distinct().order_by(Purchase.ticker).all()
                return [t[0] for t in tickers]
                
        except Exception as e:
            logger.error(f"Erro ao obter tickers: {e}")
            return []
    
    def _get_total_compras(self, user_id: int, ticker_filter: str = None) -> int:
        """Obtém total de compras para paginação"""
        try:
            with SessionLocal() as db:
                query = db.query(func.count(Purchase.id)).filter(Purchase.user_id == user_id)
                if ticker_filter:
                    query = query.filter(func.upper(Purchase.ticker) == ticker_filter.upper())
                return query.scalar() or 0
                
        except Exception as e:
            logger.error(f"Erro ao contar compras: {e}")
            return 0
    
    def search_compras(self, user_id: int, query: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Busca compras por texto"""
        try:
            offset = (page - 1) * per_page
            
            with SessionLocal() as db:
                search_pattern = f'%{query.upper()}%'
                
                # Buscar compras
                compras_query = db.query(Purchase).filter(
                    Purchase.user_id == user_id,
                    (func.upper(Purchase.ticker).like(search_pattern) | 
                     func.upper(Purchase.nome_ativo).like(search_pattern))
                ).order_by(Purchase.data_compra.desc())
                
                # Contar total
                total_compras = compras_query.count()
                
                # Aplicar paginação
                compras = compras_query.offset(offset).limit(per_page).all()
                
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
