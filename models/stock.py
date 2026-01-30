from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, index=True, nullable=False)
    empresa = Column(String(200), nullable=False)
    setor = Column(String(100))
    subsetor = Column(String(100))
    
    # Preços
    cotacao = Column(Float)
    valor_mercado = Column(Float)
    
    # Indicadores de valuation
    pl = Column(Float)  # P/L
    pvp = Column(Float)  # P/VP
    psr = Column(Float)  # P/SR
    div_yield = Column(Float)  # DY
    ev_ebit = Column(Float)  # EV/EBIT
    ev_ebitda = Column(Float)  # EV/EBITDA
    
    # Indicadores de rentabilidade
    roe = Column(Float)  # ROE
    roic = Column(Float)  # ROIC
    roa = Column(Float)  # ROA
    margem_liquida = Column(Float)  # Margem Líquida
    margem_bruta = Column(Float)  # Margem Bruta
    margem_ebit = Column(Float)  # Margem EBIT
    
    # Indicadores de endividamento
    div_liquida_patrim = Column(Float)  # Dívida Líquida/Patrimônio
    div_liquida_ebitda = Column(Float)  # Dívida Líquida/EBITDA
    patrimonio_liquido = Column(Float)  # Patrimônio Líquido
    
    # Indicadores de crescimento
    cresc_receita_5a = Column(Float)  # Crescimento Receita 5 anos
    cresc_lucro_5a = Column(Float)  # Crescimento Lucro 5 anos
    
    # Outros indicadores
    giro_ativos = Column(Float)
    liquidity = Column(Float)  # Liquidez Corrente
    
    # Campos para ranking
    score_final = Column(Float)  # Pontuação final do ranking
    rank_posicao = Column(Integer)  # Posição no ranking
    
    # Metadados
    data_atualizacao = Column(DateTime(timezone=True), server_default=func.now())
    fonte_dados = Column(String(50), default='fundamentus')
    
    def __repr__(self):
        return f'<Stock {self.ticker} - {self.empresa}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'ticker': self.ticker,
            'empresa': self.empresa,
            'setor': self.setor,
            'subsetor': self.subsetor,
            'cotacao': self.cotacao,
            'valor_mercado': self.valor_mercado,
            'pl': self.pl,
            'pvp': self.pvp,
            'psr': self.psr,
            'div_yield': self.div_yield,
            'ev_ebit': self.ev_ebit,
            'ev_ebitda': self.ev_ebitda,
            'roe': self.roe,
            'roic': self.roic,
            'roa': self.roa,
            'margem_liquida': self.margem_liquida,
            'margem_bruta': self.margem_bruta,
            'margem_ebit': self.margem_ebit,
            'div_liquida_patrim': self.div_liquida_patrim,
            'div_liquida_ebitda': self.div_liquida_ebitda,
            'patrimonio_liquido': self.patrimonio_liquido,
            'cresc_receita_5a': self.cresc_receita_5a,
            'cresc_lucro_5a': self.cresc_lucro_5a,
            'giro_ativos': self.giro_ativos,
            'liquidity': self.liquidity,
            'score_final': self.score_final,
            'rank_posicao': self.rank_posicao,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'fonte_dados': self.fonte_dados
        }