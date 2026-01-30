from models.database import SessionLocal
from models.stock import Stock

db = SessionLocal()
stock = db.query(Stock).filter(Stock.ticker == 'PETR4').first()
if stock:
    print('Ticker:', stock.ticker)
    print('Data tipo:', type(stock.data_atualizacao))
    print('Data valor:', stock.data_atualizacao)
    data_dict = stock.to_dict()
    print('Data dict tipo:', type(data_dict['data_atualizacao']))
    print('Data dict valor:', data_dict['data_atualizacao'])
else:
    print('PETR4 não encontrada')
db.close()