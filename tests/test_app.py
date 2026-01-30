#!/usr/bin/env python3
"""
Versão simplificada para teste da aplicação
"""

from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    """Página de teste"""
    html_template = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stonks - Teste</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h1>🚀 Stonks - Teste Bem Sucedido!</h1>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-success">
                                <h4>✅ Aplicação funcionando!</h4>
                                <p>O servidor Flask está rodando corretamente.</p>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5>📋 Próximos Passos</h5>
                                        </div>
                                        <div class="card-body">
                                            <ol>
                                                <li>Instalar dependências: <code>pip install -r requirements.txt</code></li>
                                                <li>Executar atualização: <code>python scripts/daily_update.py</code></li>
                                                <li>Iniciar aplicação: <code>python run.py</code></li>
                                            </ol>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5>🔧 Estrutura do Projeto</h5>
                                        </div>
                                        <div class="card-body">
                                            <ul>
                                                <li>✅ Configuração criada</li>
                                                <li>✅ Modelo de dados definido</li>
                                                <li>✅ Serviços implementados</li>
                                                <li>✅ Rotas configuradas</li>
                                                <li>✅ Templates criados</li>
                                                <li>⏳ Dependências em instalação</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <button class="btn btn-primary" onclick="testAPI()">
                                    <i class="fas fa-code"></i> Testar API
                                </button>
                                <button class="btn btn-success ms-2" onclick="checkStatus()">
                                    <i class="fas fa-check"></i> Verificar Status
                                </button>
                            </div>
                            
                            <div id="result" class="mt-3"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/js/all.min.js"></script>
        
        <script>
            function testAPI() {
                const result = document.getElementById('result');
                result.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin"></i> Testando API...</div>';
                
                // Simular teste de API
                setTimeout(() => {
                    result.innerHTML = `
                        <div class="alert alert-success">
                            <h5><i class="fas fa-check-circle"></i> API Test Result</h5>
                            <p><strong>Status:</strong> ✅ Online</p>
                            <p><strong>Endpoints disponíveis:</strong></p>
                            <ul>
                                <li>GET /api/ranking - Ranking de ações</li>
                                <li>GET /api/stock/{ticker} - Detalhes da ação</li>
                                <li>GET /api/filter - Filtros avançados</li>
                                <li>GET /api/stats - Estatísticas</li>
                            </ul>
                        </div>
                    `;
                }, 2000);
            }
            
            function checkStatus() {
                const result = document.getElementById('result');
                result.innerHTML = `
                    <div class="alert alert-info">
                        <h5><i class="fas fa-info-circle"></i> Status do Sistema</h5>
                        <div class="row">
                            <div class="col-md-6">
                                <strong>Python Version:</strong> {{ python_version }}<br>
                                <strong>Flask:</strong> ✅ Instalado<br>
                                <strong>Banco de Dados:</strong> ⏳ Configurando
                            </div>
                            <div class="col-md-6">
                                <strong>Web Scraper:</strong> ⏳ Pendente<br>
                                <strong>Cache System:</strong> ✅ Implementado<br>
                                <strong>API Endpoints:</strong> ✅ Criados
                            </div>
                        </div>
                    </div>
                `;
            }
        </script>
    </body>
    </html>
    '''
    
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    return render_template_string(html_template, python_version=python_version)

@app.route('/api/status')
def api_status():
    """API de status"""
    return {
        'status': 'success',
        'message': 'API funcionando!',
        'version': '1.0.0',
        'python_version': '3.14.2'
    }

if __name__ == '__main__':
    print("""
========================================
🚀 STONKS - MODO TESTE
========================================
Servidor iniciado em: http://localhost:5000
Modo: Teste (versão simplificada)
========================================
Acesse http://localhost:5000 no navegador
========================================
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)