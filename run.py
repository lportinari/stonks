#!/usr/bin/env python3
"""
Script principal para executar a aplicação Stonks
"""

import os
import sys
from app import create_app

def main():
    """Função principal"""
    # Verificar se estamos em ambiente de desenvolvimento
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Criar a aplicação
    app = create_app()
    
    # Configurar host e porta
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"""
========================================
STONKS - Analise de Acoes Bovespa
========================================
Servidor iniciado em: http://{host}:{port}
Modo Debug: {debug}
========================================
Acesse http://localhost:{port} no navegador
========================================
    """)
    
    # Iniciar servidor
    app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    main()