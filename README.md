# Organizaê Parêa — Projeto REST

Aplicação acadêmica de organização de tarefas por categoria, usada para demonstrar uma arquitetura REST com Cliente Web, API Gateway e dois microserviços: tarefas e categorias.

## Componentes e responsabilidades

| Parte                       | Responsabilidade                                                                        | Tecnologia                     |
| --------------------------- | --------------------------------------------------------------------------------------- | ------------------------------ |
| Bruno — Gateway             | Cadastro/login, autenticação JWT, roteamento, HATEOAS e documentação da entrada pública | FastAPI + SQLite               |
| Patricia — API de tarefas   | Criar, listar, consultar, concluir e persistir tarefas                                  | Django REST Framework + SQLite |
| Gustavo — API de categorias | Listar categorias com IDs estáveis                                                      | FastAPI                        |
| Cliente Web — grupo         | Login, escolher categoria, criar, filtrar e concluir tarefas                            | HTML, CSS e JavaScript         |

O navegador conversa somente com o Gateway. As APIs internas têm rotas próprias e o Gateway as chama por HTTP.

## Estrutura

- `gateway/`: Gateway público e autenticação JWT.
- `services/tasks/`: API Django REST Framework das tarefas.
- `services/categories/`: API FastAPI das categorias.
- `web/`: Cliente Web estático.
- `docs/contrato-api.md`: contrato de integração.
- `docs/execucao-e-apresentacao.md`: preparação local, rede do laboratório e roteiro de demonstração.
- `docs/guia-apresentacao-e-defesa.md`: explicação da arquitetura, conceitos, roteiro oral, perguntas prováveis e checklist de defesa.
- `docs/status-e-divisao-do-projeto.md`: estado atual e pendências ambientais.

## Preparar o ambiente no Windows

Na raiz do repositório, execute uma vez:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se `.env` já existir, não o sobrescreva. Mantenha valores locais e não publique esse arquivo.

Prepare o SQLite antes da primeira execução:

```powershell
.\.venv\Scripts\python.exe services/tasks/manage.py migrate
```

## Iniciar localmente

Abra quatro terminais PowerShell na raiz e inicie um processo em cada terminal:

**API de tarefas — porta 8001:**

```powershell
.\.venv\Scripts\python.exe services/tasks/manage.py runserver 127.0.0.1:8001
```

**API de categorias — porta 8002:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services/categories --port 8002
```

**Gateway — porta 8000:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir gateway --port 8000
```

**Cliente Web — porta 5500:**

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --directory web
```

Acesse `http://127.0.0.1:5500`. É possível criar uma conta na tela; para demonstração também existe a conta local `aluno` / `projeto123`, criada automaticamente quando a autenticação é usada.

Documentação interativa:

- Gateway: `http://127.0.0.1:8000/docs`
- API de tarefas: `http://127.0.0.1:8001/docs`
- API de categorias: `http://127.0.0.1:8002/docs`

## Testes automatizados

```powershell
.\.venv\Scripts\python.exe -m pytest
```

.\.venv\Scripts\python.exe -m pytest
Push-Location services/tasks
..\..\.venv\Scripts\python.exe manage.py test app
Pop-Location

## Demonstração em outra máquina

Consulte [docs/execucao-e-apresentacao.md](docs/execucao-e-apresentacao.md). Em resumo, configure `web/config.js` para apontar ao Gateway da máquina servidora, ajuste `CORS_ORIGINS`, inicie o Gateway com `--host 0.0.0.0` e permita a porta 8000 no firewall da rede privada. Os serviços internos permanecem acessíveis somente na máquina servidora.

As contas são armazenadas no SQLite local `gateway/app/users.sqlite3`; as senhas são protegidas com hash scrypt. A conta `aluno` é criada no primeiro uso quando `DEMO_ACCOUNT_ENABLED=true`. As tarefas de cada usuário ficam isoladas pelo usuário autenticado.

> Os segredos e credenciais de demonstração não são para produção. Nunca envie um `.env` real ou o banco de contas ao GitHub.
