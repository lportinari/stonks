# Integração com Modulo-Auth

Este documento descreve como configurar e usar a integração da aplicação Stonks com o serviço Modulo-Auth.

## Visão Geral

A aplicação Stonks agora utiliza o serviço **modulo-auth** para toda a autenticação e gerenciamento de usuários. Isso significa que:

- ✅ Login e registro são feitos através do modulo-auth
- ✅ Tokens JWT são usados para autenticação
- ✅ O modelo `User` foi removido do banco de dados Stonks
- ✅ A tabela `purchases` agora usa `auth_id` (UUID) em vez de `user_id` (Integer)

## Arquitetura

### Componentes Criados

1. **`services/modulo_auth_client.py`**: Cliente HTTP para comunicação com modulo-auth
2. **`services/jwt_validator.py`**: Validação de tokens JWT
3. **`services/auth_service.py`**: Serviço simplificado que repassa chamadas ao modulo-auth

### Alterações nos Modelos

- **`models/purchase.py`**: 
  - `user_id` → `auth_id` (String, UUID do modulo-auth)
  - Removido relacionamento com User

### Alterações nas Rotas

Todas as rotas que exigiam `@login_required` agora usam `@jwt_required`:

- **`routes/auth.py`**: Login, registro, logout, profile
- **`routes/purchases.py`**: CRUD de compras, dashboard

## Configuração

### 1. Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```bash
# URL do modulo-auth (usando o nome do serviço Docker)
MODULO_AUTH_URL=http://backend:3000/api

# Segredo para validar tokens JWT (deve ser o mesmo do modulo-auth)
MODULO_AUTH_JWT_SECRET=seu-jwt-secret-aqui
```

### 2. Configurar o Segredo JWT

O `MODULO_AUTH_JWT_SECRET` deve ser **IDÊNTICO** ao usado no modulo-auth. Verifique o arquivo `.env` do modulo-auth:

```bash
# No modulo-auth/.env
JWT_SECRET=seu-jwt-secret-aqui
```

### 3. Executar Migração do Banco de Dados

Execute o script de migração para atualizar a tabela `purchases`:

```bash
python -m scripts.migration.migrate_to_auth_id
```

**AVISO**: Esta migração vai ZERAR a tabela `purchases` pois não é possível converter `user_id` (Integer) para `auth_id` (UUID).

Se você tiver dados importantes que deseja preservar, precisará migrá-los manualmente.

### 4. Instalar Dependências

Atualize as dependências:

```bash
pip install -r requirements.txt
```

Isso instalará `PyJWT` (substituindo `flask-jwt-extended` e `flask-login`).

## Uso

### Login

O login agora retorna tokens JWT:

```python
# POST /auth/login
{
    "email": "usuario@exemplo.com",
    "senha": "senha123456789"
}

# Resposta
{
    "success": true,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": "uuid-do-usuario",
        "email": "usuario@exemplo.com",
        "firstName": "Nome",
        "lastName": "Sobrenome"
    }
}
```

### Registro

O registro agora exige senha de **mínimo 12 caracteres** (requisito do modulo-auth):

```python
# POST /auth/register
{
    "nome": "Nome Sobrenome",
    "email": "usuario@exemplo.com",
    "senha": "senha123456789",
    "confirmar_senha": "senha123456789"
}
```

### Uso do Token JWT

Para rotas protegidas, envie o token no header `Authorization`:

```bash
curl -H "Authorization: Bearer <access_token>" \
     http://localhost:5000/purchases/
```

Ou como cookie (para navegador):

```javascript
document.cookie = "access_token=<token>; path=/; httponly";
```

### Renovar Token

Use o refresh token para obter um novo access token:

```python
# POST /auth/api/refresh
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

# Resposta
{
    "success": true,
    "access_token": "novo-access-token...",
    "refresh_token": "mesmo-ou-novo-refresh-token..."
}
```

## Endpoints do Modulo-Auth

### Autenticação

| Endpoint | Método | Descrição |
|----------|---------|------------|
| `/api/auth/login` | POST | Fazer login |
| `/api/auth/refresh` | POST | Renovar access token |
| `/api/auth/logout` | POST | Logout do dispositivo atual |
| `/api/auth/logout-all` | POST | Logout de todos os dispositivos |

### Usuários

| Endpoint | Método | Descrição |
|----------|---------|------------|
| `/api/users` | POST | Criar novo usuário |
| `/api/users/:id` | GET | Buscar dados do usuário |
| `/api/users/:id` | PATCH | Atualizar dados do usuário |

## Diferenças no Comportamento

### Requisitos de Senha

- **Antes**: Mínimo 6 caracteres
- **Agora**: Mínimo 12 caracteres (exigido pelo modulo-auth)

### Reset de Senha

- **Antes**: Gerenciado localmente
- **Agora**: Gerenciado pelo modulo-auth (não implementado nesta integração)

### Logout

- **Antes**: Apenas removia sessão
- **Agora**: Também invalida tokens no modulo-auth

## Docker Compose

Ao executar com Docker, certifique-se de que ambos os serviços estão na mesma rede:

```yaml
version: '3.8'

services:
  stonks:
    build: .
    ports:
      - "5000:5000"
    environment:
      - MODULO_AUTH_URL=http://backend:3000/api
      - MODULO_AUTH_JWT_SECRET=seu-jwt-secret-aqui
    networks:
      - app-network

  backend:
    # modulo-auth service
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

## Troubleshooting

### Erro: "Token inválido ou expirado"

Verifique se:
1. O `MODULO_AUTH_JWT_SECRET` está correto
2. O token não expirou (tokens têm 15 minutos de validade por padrão)
3. O token está sendo enviado corretamente no header `Authorization: Bearer <token>`

### Erro: "Erro de conexão com modulo-auth"

Verifique se:
1. O `MODULO_AUTH_URL` está correto
2. O serviço modulo-auth está rodando
3. Ambos estão na mesma rede Docker

### Erro: "A senha deve ter pelo menos 12 caracteres"

Este é um requisito do modulo-auth. Use uma senha mais forte.

## Próximos Passos

### Frontend (Opcional)

Se você quiser atualizar o frontend para usar JWT:

1. Armazenar tokens em `localStorage` ou cookies
2. Enviar tokens em todas as requisições via header `Authorization`
3. Implementar renovação automática de tokens
4. Adicionar tratamento de erros 401 (não autorizado)

### Funcionalidades Extras

- [ ] Implementar reset de senha via modulo-auth
- [ ] Implementar verificação de email
- [ ] Adicionar login com Google/Outros provedores (se disponível no modulo-auth)

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs do modulo-auth
2. Verifique os logs da aplicação Stonks
3. Consulte a documentação do modulo-auth em `modulo-auth/docs/`