# Organizaê Parêa — contrato entre os componentes

Este documento é o acordo de integração para que as partes possam ser desenvolvidas em paralelo. O cliente web deve acessar somente o Gateway. O Gateway chama as APIs internas.

## Endereços locais

| Componente        | Base URL                | Responsabilidade                                  |
| ----------------- | ----------------------- | ------------------------------------------------- |
| Gateway           | `http://127.0.0.1:8000` | JWT, roteamento, composição da resposta e HATEOAS |
| API de tarefas    | `http://127.0.0.1:8001` | Criar, listar e consultar tarefas                 |
| API de categorias | `http://127.0.0.1:8002` | Listar categorias                                 |
| Cliente web       | `http://127.0.0.1:5500` | Interface do usuário                              |

## Rotas públicas do Gateway

| Método e rota           | Autenticação | Uso                                                           |
| ----------------------- | ------------ | ------------------------------------------------------------- |
| `GET /health`           | Não          | Verificar Gateway                                             |
| `POST /auth/register`   | Não          | Criar conta com `username`, `email` e `password`; retorna JWT |
| `POST /auth/token`      | Não          | Entrar com conta existente e receber JWT                      |
| `GET /auth/me`          | Bearer JWT   | Consultar usuário associado ao token                          |
| `GET /api/tasks`        | Bearer JWT   | Listar tarefas                                                |
| `GET /api/tasks/{id}`   | Bearer JWT   | Consultar tarefa                                              |
| `PATCH /api/tasks/{id}` | Bearer JWT   | Atualizar estado com `{"completed":true}` ou `false`          |
| `POST /api/tasks`       | Bearer JWT   | Criar tarefa com `{"title":"...","category_id":"estudo"}`     |
| `GET /api/categories`   | Bearer JWT   | Listar categorias                                             |
| `GET /docs`             | Não          | Swagger UI do Gateway                                         |

Cadastro usa `username` (3–32 caracteres), `email` válido e `password` (8–128 caracteres); um e-mail não pode ser reutilizado. O cadastro bem-sucedido cria a conta e já devolve um JWT. O login usa username e senha. Nomes de usuário e e-mails são normalizados para minúsculas e únicos sem distinção de maiúsculas. Senhas nunca são armazenadas em texto puro. Rotas protegidas recebem `Authorization: Bearer <token>`. As respostas de coleção têm `data` e `_links`; links contêm `href` e `method`. O cliente deve navegar pelos links devolvidos pelo Gateway, em vez de fixar rotas dos microserviços.

Cada tarefa inclui um link HATEOAS `completion` com método `PATCH`, usado para alternar seu campo `completed` sem chamar diretamente a API interna.

A conta `aluno` pode ser criada automaticamente como conta local de demonstração na primeira tentativa de cadastro/login, com credenciais definidas por `DEMO_USERNAME` e `DEMO_PASSWORD`; isso pode ser desabilitado com `DEMO_ACCOUNT_ENABLED=false`. Contas e senhas ficam no SQLite local definido por `AUTH_DATABASE_PATH`, cujo padrão é `gateway/app/users.sqlite3` e não deve ser enviado ao GitHub.

## Contrato interno das APIs

### API de tarefas (Patricia)

- `GET /tasks` retorna uma lista de objetos `{ "id": 1, "title": "...", "category_id": "estudo", "completed": false }`.
- `GET /tasks/{id}` retorna um objeto de tarefa ou HTTP 404.
- `PATCH /tasks/{id}` recebe `{ "completed": true }` ou `{ "completed": false }` e só atualiza tarefas pertencentes ao proprietário encaminhado pelo Gateway.
- `POST /tasks` recebe `{ "title": "...", "category_id": "estudo" }` e retorna a tarefa criada com HTTP 201.
- `GET /health` verifica disponibilidade.
- `GET /docs` abre a documentação Swagger/OpenAPI da API de tarefas.

O formato público da API usa `title`, `category_id` e `completed`, independentemente dos nomes internos dos campos no modelo Django. Assim, o Gateway e o Cliente Web usam o mesmo contrato; a API de tarefas faz o mapeamento para o modelo internamente.

Nas chamadas internas do Gateway para a API de tarefas, o Gateway envia `X-User-Id` a partir do `sub` verificado no JWT. A API usa esse identificador para filtrar e gravar tarefas. O Cliente Web não deve definir esse cabeçalho nem chamar a API interna diretamente.

### API de categorias (Gustavo)

- `GET /categories` retorna uma lista de objetos `{ "id": "estudo", "name": "Estudo" }`.
- `GET /health` verifica disponibilidade.
- `GET /docs` abre a documentação Swagger/OpenAPI da API de categorias.

As tarefas são persistidas no SQLite do serviço de tarefas e associadas ao usuário autenticado encaminhado pelo Gateway. Cada conta só lista e consulta as próprias tarefas. A lista de categorias é atualmente estática e mantida em memória no serviço de categorias. IDs de categorias devem permanecer strings estáveis para corresponder ao campo `category_id` nas tarefas. A API de tarefas valida os IDs contra uma cópia local dos valores aceitos, sem depender de chamada de rede à API de categorias. A lista acordada é `estudo`, `trabalho`, `pessoal`, `projetos` e `exercicio` (nome exibido: “Exercício”).
