# Organizaê Parêa — status e divisão do projeto

Este documento acompanha o estado do trabalho acadêmico do Organizaê Parêa e as últimas verificações necessárias antes da apresentação.

## Objetivo e arquitetura

O sistema permite consultar tarefas, criar uma tarefa com categoria e consultar as categorias disponíveis. O Cliente Web conversa apenas com o Gateway; o Gateway valida JWT, encaminha as chamadas HTTP para os microserviços e retorna links HATEOAS.

```text
Pessoa → Cliente Web → Gateway (JWT/HATEOAS) → API de tarefas
                                             → API de categorias
```

## Estado implementado

- **Gateway (FastAPI):** cadastra contas, armazena senhas com hash scrypt em SQLite, autentica e emite JWT; protege as rotas de tarefas e categorias; encaminha chamadas HTTP; devolve links HATEOAS; documenta rotas e erros de autenticação no Swagger; lê endereços, segredo JWT e origens CORS do `.env`.
- **API de tarefas (Django REST Framework):** cria, lista, consulta e atualiza conclusão de tarefas; valida IDs de categoria; persiste dados em SQLite associados ao usuário enviado pelo Gateway; expõe `/health` e Swagger; apresenta campos públicos `title`, `category_id` e `completed` compatíveis com o Gateway.
- **API de categorias (FastAPI):** expõe `/categories` e `/health`, documenta-se em Swagger e mantém IDs estáveis: `estudo`, `trabalho`, `pessoal`, `projetos` e `exercicio`.
- **Cliente Web:** oferece cadastro/login, criação e conclusão de tarefas, filtros (todas/a fazer/feitas), contagem de progresso, microanimações, mensagens de erro e logout. O endereço do Gateway fica em `web/config.js`, não é apresentado ao usuário.
- **Testes:** há testes de cadastro/login, hash scrypt, JWT, contrato da API de tarefas, isolamento entre usuários, categorias e um teste ponta a ponta que inicia os três serviços e acessa tarefas através do Gateway.
- **Documentação de execução:** [guia de execução e apresentação](execucao-e-apresentacao.md) e [contrato das APIs](contrato-api.md).

## Divisão original e resultado

| Integrante / parte   | Responsabilidade original                 | Estado atual                                                                                                                          |
| -------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Bruno — Gateway      | JWT, roteamento, HATEOAS, erros e Swagger | Implementado; testes automatizados cobrem autenticação, autorização, contrato público, HATEOAS, Swagger e indisponibilidade simulada. |
| Patricia — tarefas   | Criar, listar e consultar tarefas         | Implementado em Django REST Framework, com persistência SQLite, validação, contrato público comum e testes.                           |
| Gustavo — categorias | Listar categorias e definir IDs           | Implementado em FastAPI; IDs correspondem aos aceitos pela API de tarefas e existem testes.                                           |
| Grupo — Cliente Web  | Tela de tarefas e integração              | Implementado; configurável para usar Gateway remoto.                                                                                  |

## Dependências entre os serviços

As APIs são executáveis independentes. A API de tarefas não faz uma chamada de rede à API de categorias; valida `category_id` contra a lista acordada localmente. O Gateway valida o JWT e encaminha a identidade do usuário à API de tarefas, que separa as listas por conta. Portanto, há dependência de contrato (os IDs precisam coincidir), não dependência de disponibilidade entre tarefas e categorias. A lista oficial de IDs e formatos está em [contrato-api.md](contrato-api.md).

## Verificações locais automatizadas

Na raiz do repositório, execute:

```powershell
.\.venv\Scripts\python.exe -m pytest
Push-Location services/tasks
..\..\.venv\Scripts\python.exe manage.py test app
Pop-Location
```

A suíte raiz verifica Gateway, categorias e integração HTTP real; os testes Django verificam modelo, validações e formato da API de tarefas.

## Pendências que dependem do ambiente de apresentação

- [ ] Executar os comandos do [guia de execução e apresentação](execucao-e-apresentacao.md) em todos os computadores que serão usados.
- [ ] Configurar `web/config.js` com o endereço real do Gateway da máquina servidora.
- [ ] Configurar `CORS_ORIGINS` com a origem real do cliente e abrir a porta 8000 no firewall, se a rede do laboratório permitir.
- [ ] Fazer um ensaio presencial completo, incluindo login, criação de tarefa, seleção de categoria, Swagger, rejeição de chamada sem JWT e, se possível, indisponibilidade simulada.
- [ ] Confirmar que o repositório GitHub está acessível ao professor e integrantes e enviar o link. Isso não pode ser confirmado ou executado apenas pelo código local.

## Observações de segurança e escopo

As credenciais `aluno` / `projeto123` e os segredos exemplificados são somente para demonstração. Novas contas são guardadas em `gateway/app/users.sqlite3` e suas senhas são derivadas com scrypt; não publique o `.env` real nem bancos SQLite locais. A autenticação não substitui uma solução de produção. A API de tarefas usa SQLite; as categorias permanecem estáticas no código, suficiente para o escopo de demonstração.
