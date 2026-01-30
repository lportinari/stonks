# 🚀 Stonks - Análise e Ranking de Ações da Bovespa

Sistema web em Python para análise e ranking das melhores ações da Bovespa baseado em indicadores fundamentalistas como DY, P/L, P/VP, ROE, etc.

## 📋 Funcionalidades

### 🏆 Ranking de Ações
- Ranking automático baseado em múltiplos indicadores
- Sistema de pontuação configurável pelo usuário
- Filtros por setor e indicadores
- Comparação entre múltiplas ações

### 📊 Indicadores Analisados
- **DY (Dividend Yield)**: Retorno por dividendos
- **P/L (Price-to-Earnings)**: Múltiplo preço/lucro
- **P/VP (Price-to-Book Value)**: Múltiplo preço/valor patrimonial
- **ROE (Return on Equity)**: Retorno sobre patrimônio líquido
- **Margem Líquida**: Rentabilidade da empresa
- **ROIC**: Retorno sobre capital investido
- **Liquidez**: Saúde financeira

### 🎯 Funcionalidades Principais
- Dashboard interativo com ranking em tempo real
- Filtros avançados por indicadores
- Comparação lado a lado entre ações
- Sistema de pesos configurável para cada indicador
- Exportação de dados para CSV
- API REST para integração
- Atualização automática diária dos dados

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask**: Framework web Python
- **SQLAlchemy**: ORM para banco de dados
- **BeautifulSoup**: Web scraping (Fundamentus)
- **Pandas**: Manipulação de dados
- **NumPy**: Cálculos numéricos

### Frontend
- **Bootstrap 5**: Framework CSS responsivo
- **Chart.js**: Visualizações gráficas
- **Font Awesome**: Ícones

### Fontes de Dados
- **Fundamentus**: Dados fundamentalistas brasileiros
- **Yahoo Finance**: Backup e dados complementares

## 📦 Estrutura do Projeto

```
stonks/
├── app.py                 # Aplicação Flask principal
├── run.py                 # Script para executar a aplicação
├── config.py              # Configurações do sistema
├── requirements.txt        # Dependências Python
├── .env                   # Variáveis de ambiente
├── models/                # Modelos de dados
│   ├── __init__.py
│   ├── database.py        # Configuração do banco
│   └── stock.py          # Modelo de ações
├── services/              # Lógica de negócio
│   ├── __init__.py
│   ├── fundamentus_scraper.py    # Scraping de dados
│   ├── indicator_calculator.py   # Cálculo de indicadores
│   ├── ranking_service.py         # Sistema de ranking
│   └── cache_manager.py          # Gerenciamento de cache
├── routes/                # Rotas da aplicação
│   ├── __init__.py
│   ├── main.py           # Rotas principais
│   └── api.py           # Endpoints de API
├── templates/            # Templates HTML
│   ├── base.html
│   ├── index.html
│   └── static/          # CSS, JS e imagens
├── scripts/             # Scripts de automação e manutenção
│   ├── daily_update.py   # Atualização diária principal
│   ├── maintenance/      # Scripts de manutenção
│   │   ├── fix_scores.py    # Correção de scores
│   │   ├── check_stocks.py  # Verificação de sincronia
│   │   └── diagnose.py      # Diagnóstico do sistema
│   ├── updaters/        # Scripts de atualização de dados
│   │   ├── update_real_data.py    # Atualização geral
│   │   ├── update_real_prices.py   # Atualização de preços
│   │   ├── get_real_quotes.py      # Obtenção de cotações
│   │   ├── quick_update_real.py    # Update rápido
│   │   └── create_sample_data.py   # Dados de teste
│   ├── finders/         # Scripts de busca de ações
│   │   ├── b3_stock_finder.py       # Buscador B3
│   │   └── simple_stock_finder.py   # Buscador simples
│   └── schedulers/      # Scripts de agendamento
│       ├── continuous_updater.py     # Atualizador contínuo
│       └── rotating_updater.py      # Atualizador rotativo
├── tests/               # Suite de testes
│   ├── test_app.py      # Testes da aplicação
│   ├── test_complete.py # Testes completos
│   ├── test_interface_fix.py # Testes de interface
│   ├── test_real_data.py # Testes com dados reais
│   ├── test_scraping.py # Testes de scraping
│   ├── test_simple_api.py # Testes de API
│   └── test_simple.py   # Testes simples
├── docs/                # Documentação adicional
│   ├── README_PROFESSIONAL_APIS.md # APIs profissionais
│   └── README_ROTATIVO.md # Sistema rotativo
├── database/            # Banco de dados SQLite
├── logs/                # Logs da aplicação
├── data/                # Dados auxiliares
└── reports/             # Relatórios gerados
```

## 🚀 Instalação e Configuração

### 1. Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 2. Clonar o projeto
```bash
git clone <repository-url>
cd stonks
```

### 3. Criar ambiente virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 4. Instalar dependências
```bash
pip install -r requirements.txt
```

### 5. Configurar variáveis de ambiente

**IMPORTANTE**: O projeto agora usa variáveis de ambiente para chaves de API!

1. Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` com suas chaves:
```env
SECRET_KEY=stonks-secret-key-2024
DATABASE_URL=sqlite:///database/stocks.db

# Chaves de API (OBRIGATÓRIO)
BRAPI_API_KEY=sua_chave_brapi_aqui
ALPHAVANTAGE_API_KEY=sua_chave_alphavantage_aqui
```

3. **Obtenha suas chaves**:
   - **BrAPI**: https://brapi.dev/ (API brasileira - recomendada)
   - **Alpha Vantage**: https://www.alphavantage.co/support/#api-key (fallback)

**⚠️ Aviso**: Sem as chaves de API, algumas funcionalidades podem não funcionar corretamente.

### 6. Executar a aplicação
```bash
python run.py
```

Acesse `http://localhost:5000` no navegador.

## 📡 Uso da API

### Endpoints Principais

#### Obter Ranking Completo
```http
GET /api/ranking?limit=50&sector=Financeiro
```

#### Detalhes de uma Ação
```http
GET /api/stock/PETR4
```

#### Comparar Ações
```http
GET /api/compare?tickers=PETR4,VALE3,ITUB4
```

#### Filtrar Ações
```http
GET /api/filter?min_dy=0.05&max_pl=20&min_roe=0.15
```

#### Obter Estatísticas
```http
GET /api/stats
```

## ⚙️ Configuração dos Pesos

O sistema permite configurar os pesos de cada indicador no ranking:

### Padrão:
- DY (Dividend Yield): 25%
- P/L: 20%
- P/VP: 20%
- ROE: 20%
- Margem Líquida: 15%

### Como Configurar:
1. Acesse a página "Config" na aplicação
2. Ajuste os pesos desejados
3. A soma deve ser igual a 100%
4. Salve para recalcular o ranking

## 🔄 Atualização Automática

### Script Diário
O script `scripts/daily_update.py` pode ser executado manualmente ou agendado:

#### Execução Manual:
```bash
python scripts/daily_update.py
```

#### Agendamento (Linux/Mac - crontab):
```bash
# Executar todos os dias às 18:00
0 18 * * * cd /path/to/stonks && python scripts/daily_update.py
```

#### Agendamento (Windows - Task Scheduler):
- Abrir "Task Scheduler"
- Criar nova tarefa
- Configurar para executar diariamente
- Comando: `python C:\path\to\stonks\scripts\daily_update.py`

## 📊 Relatórios

O sistema gera relatórios automáticos:
- Relatório diário de atualização
- Estatísticas do ranking
- Top 10 ações por setor
- Evolução temporal dos indicadores

Os relatórios são salvos na pasta `reports/`.

## 🔧 Desenvolvimento

### Estrutura de Código
- **Models**: Definição das entidades do banco de dados
- **Services**: Lógica de negócio e regras de cálculo
- **Routes**: Controladores Flask e endpoints da API
- **Templates**: Interface web com Bootstrap

### Padrões Utilizados
- Blueprint para organização de rotas
- SQLAlchemy ORM para persistência
- Cache para otimização de performance
- Logging para monitoramento e debug

### Adicionando Novos Indicadores
1. Adicionar campo no modelo `Stock`
2. Atualizar scraper para coletar o dado
3. Implementar cálculo em `IndicatorCalculator`
4. Adicionar peso na configuração
5. Atualizar interface web

## 🐛 Troubleshooting

### Problemas Comuns

#### Erro de Conexão com Fundamentus
- Verificar conexão com internet
- Confirmar se o site está acessível
- Verificar se o IP não foi bloqueado

#### Dados Não Atualizados
- Executar script de atualização manualmente
- Verificar logs em `daily_update.log`
- Limpar cache via interface ou API

#### Erro no Banco de Dados
- Verificar se o diretório `database/` existe
- Confirmar permissões de escrita
- Recriar banco apagando arquivo `stocks.db`

### Logs
- `stonks.log`: Logs da aplicação
- `daily_update.log`: Logs da atualização diária

## 📝 Licença e Disclaimer

**IMPORTANTE**: Este projeto é para fins educacionais e de pesquisa. Não constitui recomendação de investimento. Sempre faça sua própria análise antes de investir.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:
1. Fork do projeto
2. Criar branch para sua feature
3. Commit das mudanças
4. Pull request

## 📞 Contato

Desenvolvido com ❤️ para a comunidade de investidores brasileiros.

---

**⚠️ Aviso Legal**: As informações fornecidas neste sistema não constituem recomendação de investimento. Investimentos envolvem riscos e você pode perder dinheiro. Consulte sempre um profissional qualificado antes de tomar decisões de investimento.