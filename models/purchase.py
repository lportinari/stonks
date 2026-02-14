from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, date

class Purchase(Base):
    """Modelo de Compra usando SQLAlchemy ORM"""
    __tablename__ = 'purchases'
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    nome_ativo = Column(String(200))
    
    # Dados da compra
    quantidade = Column(Float, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    taxas = Column(Float, default=0.0)
    custo_total = Column(Float, nullable=False)
    preco_medio = Column(Float, nullable=False)
    data_compra = Column(DateTime(timezone=True), nullable=False)
    classe_ativo = Column(String(20))  # 'acao', 'fii', 'etf', 'bdr'
    
    # Venda (opcional)
    quantidade_vendida = Column(Integer, default=0)
    preco_venda = Column(Float)
    data_venda = Column(DateTime(timezone=True))
    
    # Metadados
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamento com usuário
    # user = relationship("User", back_populates="purchases")
    
    def __repr__(self):
        return f'<Purchase {self.ticker} - {self.quantidade} unidades>'
    
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

# Funções helper para operações de compras
def create_purchase(user_id, ticker, nome_ativo, quantidade, preco_unitario, taxas=0.0, data_compra=None, classe_ativo=None):
    """Cria uma nova compra usando ORM"""
    from .database import SessionLocal
    
    if data_compra is None:
        data_compra = datetime.now()
    
    # Calcular custo total e preço médio
    quantidade = float(quantidade)
    preco_unitario = float(preco_unitario)
    taxas = float(taxas)
    custo_total = (quantidade * preco_unitario) + taxas
    preco_medio = custo_total / quantidade
    
    with SessionLocal() as db:
        purchase = Purchase(
            user_id=user_id,
            ticker=ticker.upper(),
            nome_ativo=nome_ativo,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
            taxas=taxas,
            custo_total=custo_total,
            preco_medio=preco_medio,
            data_compra=data_compra,
            classe_ativo=classe_ativo
        )
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        return purchase.id

def get_purchases_by_user(user_id, limit=50, offset=0, order_by='data_compra', order_dir='DESC'):
    """Busca compras de um usuário com paginação usando ORM"""
    from .database import SessionLocal
    
    with SessionLocal() as db:
        query = db.query(Purchase).filter(Purchase.user_id == user_id)
        
        # Aplicar ordenação
        order_column = getattr(Purchase, order_by, Purchase.data_compra)
        if order_dir.upper() == 'DESC':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        # Aplicar paginação
        purchases = query.offset(offset).limit(limit).all()
        
        return purchases

def get_purchase_by_id(purchase_id, user_id):
    """Busca uma compra específica do usuário usando ORM"""
    from .database import SessionLocal
    
    with SessionLocal() as db:
        return db.query(Purchase).filter(
            Purchase.id == purchase_id,
            Purchase.user_id == user_id
        ).first()

def update_purchase(purchase_id, user_id, **kwargs):
    """Atualiza uma compra usando ORM"""
    from .database import SessionLocal
    
    allowed_fields = ['ticker', 'nome_ativo', 'quantidade', 'preco_unitario', 'taxas', 'data_compra']
    
    with SessionLocal() as db:
        purchase = db.query(Purchase).filter(
            Purchase.id == purchase_id,
            Purchase.user_id == user_id
        ).first()
        
        if not purchase:
            return False
        
        # Atualizar campos permitidos
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(purchase, field, value)
        
        # Recalcular custo total e preço médio se necessário
        if 'quantidade' in kwargs or 'preco_unitario' in kwargs or 'taxas' in kwargs:
            purchase.custo_total = (purchase.quantidade * purchase.preco_unitario) + purchase.taxas
            purchase.preco_medio = purchase.custo_total / purchase.quantidade if purchase.quantidade > 0 else 0
        
        db.commit()
        return True

def delete_purchase(purchase_id, user_id):
    """Deleta uma compra usando ORM"""
    from .database import SessionLocal
    
    with SessionLocal() as db:
        purchase = db.query(Purchase).filter(
            Purchase.id == purchase_id,
            Purchase.user_id == user_id
        ).first()
        
        if not purchase:
            return False
        
        db.delete(purchase)
        db.commit()
        return True

def get_portfolio_summary(user_id):
    """Resume o portfolio do usuário usando ORM"""
    from .database import SessionLocal
    from sqlalchemy import func, and_
    
    try:
        with SessionLocal() as db:
            result = db.query(
                func.count(Purchase.id).label('total_compras'),
                func.sum(Purchase.custo_total).label('total_investido'),
                func.sum(Purchase.quantidade).label('total_ativos'),
                func.count(func.distinct(Purchase.ticker)).label('total_tickers'),
                func.avg(Purchase.preco_medio).label('preco_medio_geral')
            ).filter(Purchase.user_id == user_id).first()
            
            return {
                'total_compras': result.total_compras or 0,
                'total_investido': float(result.total_investido) if result.total_investido else 0.0,
                'total_ativos': result.total_ativos or 0,
                'total_tickers': result.total_tickers or 0,
                'preco_medio_geral': float(result.preco_medio_geral) if result.preco_medio_geral else 0.0
            }
    except Exception as e:
        print(f"Erro ao obter resumo do portfolio: {e}")
        return {
            'total_compras': 0,
            'total_investido': 0.0,
            'total_ativos': 0,
            'total_tickers': 0,
            'preco_medio_geral': 0.0
        }

def get_purchases_by_ticker(user_id, ticker):
    """Busca compras de um ticker específico usando ORM"""
    from .database import SessionLocal
    
    with SessionLocal() as db:
        return db.query(Purchase).filter(
            Purchase.user_id == user_id,
            Purchase.ticker == ticker.upper()
        ).order_by(Purchase.data_compra.asc()).all()

def get_portfolio_distribution(user_id):
    """Busca distribuição do portfolio por ticker usando ORM"""
    from .database import SessionLocal
    from sqlalchemy import func
    
    try:
        with SessionLocal() as db:
            results = db.query(
                Purchase.ticker,
                Purchase.nome_ativo,
                func.sum(Purchase.quantidade).label('total_quantidade'),
                func.sum(Purchase.custo_total).label('total_custo'),
                func.avg(Purchase.preco_medio).label('preco_medio'),
                func.count(Purchase.id).label('num_compras')
            ).filter(
                Purchase.user_id == user_id
            ).group_by(
                Purchase.ticker,
                Purchase.nome_ativo
            ).order_by(
                func.sum(Purchase.custo_total).desc()
            ).all()
            
            return [
                {
                    'ticker': r.ticker,
                    'nome_ativo': r.nome_ativo,
                    'total_quantidade': r.total_quantidade or 0,
                    'total_custo': float(r.total_custo) if r.total_custo else 0.0,
                    'preco_medio': float(r.preco_medio) if r.preco_medio else 0.0,
                    'num_compras': r.num_compras or 0
                }
                for r in results
            ]
    except Exception as e:
        print(f"Erro ao obter distribuição do portfolio: {e}")
        return []

def get_portfolio_performance(user_id):
    """Calcula performance do portfolio usando ORM"""
    from .database import SessionLocal
    from sqlalchemy import func
    
    with SessionLocal() as db:
        # Buscar dados agrupados por ticker
        ticker_data = db.query(
            Purchase.ticker,
            Purchase.nome_ativo,
            func.sum(Purchase.quantidade).label('total_quantidade'),
            func.sum(Purchase.custo_total).label('total_custo'),
            func.avg(Purchase.preco_medio).label('preco_medio_calculado')
        ).filter(
            Purchase.user_id == user_id
        ).group_by(
            Purchase.ticker,
            Purchase.nome_ativo
        ).order_by(
            func.sum(Purchase.custo_total).desc()
        ).all()
        
        performance_data = []
        total_investido = 0.0
        
        for ticker_info in ticker_data:
            ticker = ticker_info.ticker
            quantidade = ticker_info.total_quantidade or 0
            custo_total = float(ticker_info.total_custo) if ticker_info.total_custo else 0.0
            preco_medio_calculado = float(ticker_info.preco_medio_calculado) if ticker_info.preco_medio_calculado else 0.0
            
            total_investido += custo_total
            
            # Simular preço atual (em produção, buscar de API)
            preco_atual = preco_medio_calculado * (1 + (hash(ticker) % 20 - 10) / 100)
            valor_atual = quantidade * preco_atual
            resultado = valor_atual - custo_total
            resultado_percentual = (resultado / custo_total) * 100 if custo_total > 0 else 0.0
            
            performance_data.append({
                'ticker': ticker,
                'nome_ativo': ticker_info.nome_ativo,
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
        resultado_percentual_total = (resultado_total / total_investido) * 100 if total_investido > 0 else 0.0
        
        return {
            'tickers': performance_data,
            'resumo': {
                'total_investido': total_investido,
                'valor_atual_total': valor_atual_total,
                'resultado_total': resultado_total,
                'resultado_percentual_total': resultado_percentual_total
            }
        }

def get_portfolio_distribution_by_asset_class(user_id):
    """Calcula a distribuição do portfolio por classe de ativo usando ORM"""
    from .database import SessionLocal
    from sqlalchemy import func
    
    try:
        with SessionLocal() as db:
            # Buscar dados agrupados por classe de ativo
            results = db.query(
                Purchase.classe_ativo,
                func.sum(Purchase.custo_total).label('total_custo'),
                func.count(Purchase.id).label('num_compras'),
                func.count(func.distinct(Purchase.ticker)).label('num_tickers')
            ).filter(
                Purchase.user_id == user_id
            ).group_by(
                Purchase.classe_ativo
            ).order_by(
                func.sum(Purchase.custo_total).desc()
            ).all()
            
            # Calcular total investido
            total_investido = sum(float(r.total_custo) if r.total_custo else 0.0 for r in results)
            
            # Mapeamento de nomes para exibição
            classe_nomes = {
                'acoes': 'Ações',
                'renda_fixa_pos': 'Renda Fixa Pós',
                'renda_fixa_dinamica': 'Renda Fixa Dinâmica',
                'fundos_imobiliarios': 'Fundos Imobiliários',
                'internacional': 'Internacional',
                'fundos_multimercados': 'Fundos Multimercados',
                'alternativos': 'Alternativos'
            }
            
            # Construir resultado
            distribution = []
            for r in results:
                classe = r.classe_ativo or 'Outros'
                custo = float(r.total_custo) if r.total_custo else 0.0
                percentual = (custo / total_investido * 100) if total_investido > 0 else 0.0
                
                distribution.append({
                    'classe_ativo': classe,
                    'classe_nome': classe_nomes.get(classe, classe),
                    'valor_total': custo,
                    'percentual': percentual,
                    'num_compras': r.num_compras or 0,
                    'num_tickers': r.num_tickers or 0
                })
            
            return {
                'distribution': distribution,
                'total_investido': total_investido,
                'total_classes': len(distribution)
            }
    except Exception as e:
        print(f"Erro ao obter distribuição por classe de ativo: {e}")
        return {
            'distribution': [],
            'total_investido': 0.0,
            'total_classes': 0
        }
