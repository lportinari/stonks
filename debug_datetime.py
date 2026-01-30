from models.database import SessionLocal
from models.stock import Stock

db = SessionLocal()
stock = db.query(Stock).filter(Stock.ticker == 'PETR4').first()
if stock:
    print('Stock encontrado')
    print('Data:', stock.data_atualizacao)
    print('Tipo:', type(stock.data_atualizacao))
    # Tentar chamar strftime para ver se dá erro
    try:
        print('strftime:', stock.data_atualizacao.strftime('%d/%m/%Y'))
    except Exception as e:
        print('Erro no strftime:', e)
        print('Tipo:', type(stock.data_atualizacao))
else:
    print('Stock não encontrado')
db.close()