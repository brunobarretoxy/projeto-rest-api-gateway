# Contrato inicial entre os componentes

Este documento é o acordo de integração para que as partes possam ser desenvolvidas em paralelo. O cliente web deve acessar somente o Gateway. O Gateway chama as APIs internas.

## Endereços locais

| Componente        | Base URL                | Responsabilidade                                  |
| ----------------- | ----------------------- | ------------------------------------------------- |
| Gateway           | `http://127.0.0.1:8000` | JWT, roteamento, composição da resposta e HATEOAS |
| API de tarefas    | `http://127.0.0.1:8001` | Criar e listar tarefas                            |
| API de categorias | `http://127.0.0.1:8002` | Listar categorias                                 |
| Cliente web       | `http://127.0.0.1:5500` | Interface do usuário                              |

## Rotas públicas do Gateway

| Método e rota           | Autenticação | Uso                                                                  |
| ----------------------- | ------------ | -------------------------------------------------------------------- |
| `GET /health`           | Não          | Verificar Gateway                                                    |
| `POST /auth/demo-token` | Não          | Receber JWT, enviando `{"username":"aluno","password":"projeto123"}` |
| `GET /api/tasks`        | Bearer JWT   | Listar tarefas                                                       |
| `GET /api/tasks/{id}`   | Bearer JWT   | Consultar tarefa                                                     |
| `POST /api/tasks`       | Bearer JWT   | Criar tarefa com `{"title":"...","category_id":"estudo"}`            |
| `GET /api/categories`   | Bearer JWT   | Listar categorias                                                    |
| `GET /docs`             | Não          | Swagger UI do Gateway                                                |

Rotas de API protegidas recebem `Authorization: Bearer <token>`. As respostas de coleção têm `data` e `_links`; links contêm `href` e `method`. O cliente deve navegar pelos links devolvidos pelo Gateway, em vez de fixar rotas dos microserviços.

## Contrato interno das APIs

### API de tarefas (Patricia)

- `GET /tasks` retorna uma lista de objetos `{ "id": 1, "title": "...", "category_id": "estudo", "completed": false }`.
- `GET /tasks/{id}` retorna um objeto de tarefa ou HTTP 404.
- `POST /tasks` recebe `{ "title": "...", "category_id": "estudo" }` e retorna a tarefa criada com HTTP 201.
- `GET /health` verifica disponibilidade.

### API de categorias (Gustavo)

- `GET /categories` retorna uma lista de objetos `{ "id": "estudo", "name": "Estudo" }`.
- `GET /health` verifica disponibilidade.

As listas iniciais são em memória e reiniciam ao parar o processo; persistência fica como possível melhoria. IDs de categorias devem permanecer strings estáveis para corresponder ao campo `category_id` nas tarefas.
