from flask import Flask
from config import Config
from models import init_db
from routes import main_bp, auth_bp, purchases_bp, login_manager
from routes.api import api_bp
import logging
import os

def create_app():
    """Função factory para criar a aplicação Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configurar logging
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(message)s',
            handlers=[
                logging.FileHandler('stonks.log'),
                logging.StreamHandler()
            ]
        )
    
    # Inicializar banco de dados
    with app.app_context():
        init_db()
    
    # Configurar Flask-Login
    login_manager.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(purchases_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)