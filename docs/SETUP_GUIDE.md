# 🚀 Guia de Configuração - Stonks

## 📋 Visão Geral

Este guia documenta como configurar o projeto Stonks em uma nova máquina, incluindo a solução para problemas comuns de configuração do banco de dados.

## ⚠️ Problema Conhecido: AttributeError: 'User' has no attribute 'query'

### Causa do Problema
O projeto mistura dois padrões diferentes de acesso a banco de dados:
- **SQLAlchemy ORM**: Espera que modelos tenham o método `query`
- **SQLite direto**: Implementa funções manuais como `get_user_by_email`, `get_user_by_id`

O Flask-Login espera o padrão SQLAlchemy, mas o modelo User usa SQLite direto.

### ✅ Solução
Siga exatamente os passos abaixo para configurar corretamente:

---

## 🛠️ Passo a Passo de Configuração

### 1. Pré-requisitos

```bash
# Verificar versão do Python (requer Python 3.8+)
python --version

# Verificar se pip está instalado
pip --version
```

### 2. Clonar o Projeto

```bash
git clone https://github.com/lportinari/stonks.git
cd stonks
```

### 3. Criar Ambiente Virtual

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar Dependências

```bash
pip install -r requirements.txt
```

**Importante**: Verifique se todas as dependências foram instaladas:
```bash
pip list | grep -E "(flask|sqlalchemy|bcrypt|requests)"
```

### 5. Configurar Variáveis de Ambiente

Crie o arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=stonks-secret-key-2024
DATABASE_URL=sqlite:///database/stocks.db

# Chaves de API (OBRIGATÓRIO)
BRAPI_API_KEY=sua_chave_brapi_aqui
ALPHAVANTAGE_API_KEY=sua_chave_alphavantage_aqui

# Configurações de Email (opcional, para verificação por email)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app
FROM_EMAIL=seu_email@gmail.com

# Ambiente
FLASK_ENV=development
BASE_URL=http://localhost:5000
```

**Obtenção das Chaves API:**
- **BrAPI**: Acesse https://brapi.dev/ e cadastre-se para obter chave gratuita
- **Alpha Vantage**: Acesse https://www.alphavantage.co/support/#api-key

### 6. Inicializar o Banco de Dados

Este é o passo **CRÍTICO** para evitar o erro de `User.query`:

```bash
python scripts/init_database.py
```

Este script irá:
- Criar o diretório `database/` se não existir
- Criar todas as tabelas necessárias
- Inserir usuário administrador padrão
- Configurar índices para performance

**Saída esperada:**
```
==================================================
INICIALIZAÇÃO DO BANCO DE DADOS - STONKS
==================================================

🆕 Criando banco de dados do zero...
Inicializando banco de dados: c:\path\to\stonks\database\stocks.db
✓ Tabelas criadas com sucesso!
✓ Usuário administrador criado: admin@stonks.com / admin123

✅ Banco de dados inicializado com sucesso!
```

### 7. Verificar Estrutura do Banco de Dados

```bash
# Verificar se o arquivo foi criado
ls -la database/stocks.db

# Verificar tabelas (opcional)
sqlite3 database/stocks.db ".tables"
```

### 8. Testar a Aplicação

```bash
python run.py
```

Acesse `http://localhost:5000` no navegador.

**Login inicial:**
- Email: `admin@stonks.com`
- Senha: `admin123`

---

## 🔧 Solução de Problemas

### Problema 1: AttributeError: 'User' has no attribute 'query'

**Sintomas:**
```
AttributeError: type object 'User' has no attribute 'query'
```

**Causa:** O banco de dados não foi inicializado corretamente ou o modelo User está sendo usado de forma incorreta.

**Solução:**
1. **Pare a aplicação** (Ctrl+C)
2. **Reinicialize o banco de dados:**
   ```bash
   python scripts/init_database.py
   ```
3. **Verifique se o arquivo `database/stocks.db` existe**
4. **Reinicie a aplicação:**
   ```bash
   python run.py
   ```

### Problema 2: Erro de importação - módulos não encontrados

**Sintomas:**
```
ModuleNotFoundError: No module named 'models.user'
ImportError: cannot import name 'User'
```

**Solução:**
1. **Verifique se está no diretório correto:**
   ```bash
   cd stonks
   pwd
   ```
2. **Ative o ambiente virtual:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```
3. **Reinstale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

### Problema 3: Erro de permissão no banco de dados

**Sintomas:**
```
sqlite3.OperationalError: unable to open database file
PermissionError: [Errno 13] Permission denied
```

**Solução:**
1. **Verifique permissões do diretório:**
   ```bash
   chmod 755 database/
   ```
2. **Crie o diretório manualmente:**
   ```bash
   mkdir -p database
   ```
3. **Execute o script de inicialização novamente:**
   ```bash
   python scripts/init_database.py
   ```

### Problema 4: Porta já em uso

**Sintomas:**
```
OSError: [Errno 98] Address already in use
```

**Solução:**
1. **Mude a porta em `run.py`:**
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)
   ```
2. **Ou mate o processo na porta:**
   ```bash
   # Linux/Mac
   sudo lsof -ti:5000 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

---

## 📁 Estrutura de Arquivos Essenciais

Após a configuração, verifique se os seguintes arquivos existem:

```
stonks/
├── .env                    # ✅ Variáveis de ambiente
├── database/
│   └── stocks.db          # ✅ Banco de dados SQLite
├── venv/                  # ✅ Ambiente virtual
├── logs/                  # ✅ Logs (criado automaticamente)
├── requirements.txt        # ✅ Dependências
├── app.py                 # ✅ Aplicação Flask
├── config.py              # ✅ Configurações
├── run.py                 # ✅ Script de execução
└── scripts/
    └── init_database.py   # ✅ Script de inicialização
```

---

## 🔄 Manutenção do Sistema

### Atualização Diária Automática

```bash
# Executar manualmente
python scripts/daily_update.py

# Agendar no Linux/Mac (crontab)
0 18 * * * cd /path/to/stonks && python scripts/daily_update.py

# Agendar no Windows (Task Scheduler)
# Programa: python
# Argumentos: C:\path\to\stonks\scripts\daily_update.py
```

### Backup do Banco de Dados

```bash
# Criar backup
cp database/stocks.db database/stocks_backup_$(date +%Y%m%d).db

# Restaurar backup
cp database/stocks_backup_YYYYMMDD.db database/stocks.db
```

### Limpeza de Logs

```bash
# Limpar logs antigos
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 🌐 Configuração para Produção

### 1. Variáveis de Produção

```env
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_muito_forte
DATABASE_URL=postgresql://user:pass@localhost/stonks_prod
```

### 2. Servidor WSGI (Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 3. Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📞 Suporte e Debug

### Logs Úteis

- **Aplicação**: `stonks.log`
- **Atualização**: `daily_update.log`
- **Debug**: Adicione `app.debug = True` em `app.py`

### Comandos de Debug

```bash
# Verificar tabelas do banco
sqlite3 database/stocks.db ".schema"

# Verificar usuários
sqlite3 database/stocks.db "SELECT * FROM users;"

# Testar importações
python -c "from models.user import User; print('OK')"
```

### Controle de Versão

```bash
# Verificar status
git status

# Adicionar arquivos de configuração ao .gitignore
echo ".env" >> .gitignore
echo "database/stocks.db" >> .gitignore
```

---

## ✅ Checklist de Configuração

- [ ] Python 3.8+ instalado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas via `pip install -r requirements.txt`
- [ ] Arquivo `.env` configurado com chaves API
- [ ] Banco de dados inicializado com `python scripts/init_database.py`
- [ ] Arquivo `database/stocks.db` criado
- [ ] Aplicação inicia com `python run.py`
- [ ] Login com admin@stonks.com / admin123 funciona
- [ ] Página principal carrega sem erros
- [ ] API endpoints respondem corretamente

---

## 🚀 Próximos Passos

Após a configuração bem-sucedida:

1. **Altere a senha do administrador**
2. **Configure suas chaves de API**
3. **Explore a interface web**
4. **Teste a API com `curl` ou Postman**
5. **Configure a atualização automática**
6. **Monitore os logs regularmente**

---

**Importante**: Este projeto foi projetado para funcionar com o padrão SQLite direto para o modelo User. Não tente converter para SQLAlchemy ORM sem modificar todo o sistema de autenticação.