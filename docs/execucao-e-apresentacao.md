# Organizaê Parêa — execução e apresentação

Este guia descreve a execução local e a demonstração em duas máquinas. No uso normal, o navegador acessa o Cliente Web, que chama apenas o Gateway. As APIs internas ficam atrás do Gateway.

## Pré-requisitos

- Python 3.12 ou superior (Django 6 requer Python 3.12+).
- Quatro terminais PowerShell na raiz do repositório.
- Dependências instaladas a partir do `requirements.txt` da raiz.
- Cópia local de `.env.example` chamada `.env`.

## Execução local em um computador

Na raiz, prepare o ambiente uma única vez:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se `.env` já existir, não o sobrescreva; mantenha suas configurações locais.

Antes do primeiro início (e sempre que forem adicionadas migrações), crie/atualize o banco SQLite:

```powershell
.\.venv\Scripts\python.exe services/tasks/manage.py migrate
```

Inicie cada componente em um terminal separado, todos abertos na raiz do projeto:

**API de tarefas (Django REST Framework):**

```powershell
.\.venv\Scripts\python.exe services/tasks/manage.py runserver 127.0.0.1:8001
```

**API de categorias (FastAPI):**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services/categories --port 8002
```

**Gateway (FastAPI):**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir gateway --port 8000
```

**Cliente Web estático:**

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --directory web
```

Abra `http://127.0.0.1:5500`. Cadastre uma conta informando usuário, e-mail e senha, ou use as credenciais locais definidas por `DEMO_USERNAME` e `DEMO_PASSWORD` no `.env`; os valores iniciais de demonstração são `aluno` e `projeto123`. A conta de demonstração é criada no primeiro uso se `DEMO_ACCOUNT_ENABLED=true`. Cada conta vê somente as próprias tarefas.

Documentação interativa:

- Gateway: `http://127.0.0.1:8000/docs`
- API de tarefas: `http://127.0.0.1:8001/docs`
- API de categorias: `http://127.0.0.1:8002/docs`

O SQLite guarda tarefas e contas entre reinícios (`services/tasks/db.sqlite3` e `gateway/app/users.sqlite3`). Senhas de contas são armazenadas como hash scrypt. Categorias são uma lista fixa definida no serviço de categorias; os bancos locais estão excluídos do Git.

## Testes

Na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m pytest
Push-Location services/tasks
..\..\.venv\Scripts\python.exe manage.py test app
Pop-Location
```

## Demonstração em duas máquinas na rede do laboratório

A topologia mais simples é executar Gateway e as duas APIs na máquina servidora, mantendo as APIs internas acessíveis apenas localmente. O Cliente Web pode ser servido na máquina principal. Apenas a porta 8000 do servidor precisa ser acessível pelo navegador cliente.

1. Descubra o IPv4 da máquina servidora com `ipconfig` (exemplo: `192.168.1.50`).
2. No `.env` do servidor, ajuste:

```dotenv
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
TASKS_API_URL=http://127.0.0.1:8001
CATEGORIES_API_URL=http://127.0.0.1:8002
```

3. No `web/config.js` servido na máquina principal, configure o endereço público do Gateway:

```javascript
window.APP_CONFIG = {
  gatewayBaseUrl: "http://192.168.1.50:8000",
};
```

Substitua pelo IPv4 real. Caso o navegador abra a página pelo IP da máquina principal em vez de `localhost`, inclua essa origem também em `CORS_ORIGINS`, por exemplo `http://192.168.1.60:5500`.

4. Inicie o Gateway permitindo conexões de rede na máquina servidora:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir gateway --host 0.0.0.0 --port 8000
```

As APIs internas podem continuar ligadas somente a `127.0.0.1`, pois o Gateway e elas estão na mesma máquina.

5. Se o Firewall do Windows solicitar, permita o acesso à porta 8000 na rede privada do laboratório. Não abra as portas 8001 e 8002 para o cliente; o Gateway deve ser o ponto de entrada.
6. Na máquina principal, inicie o Cliente Web e abra `http://localhost:5500`.
7. Se a página não conseguir acessar o Gateway, confira o endereço em `web/config.js`, a origem em `CORS_ORIGINS`, o firewall e se os três serviços da máquina servidora estão ativos.

A rede e as políticas do laboratório podem impor restrições que o código não consegue resolver. Faça esse teste presencialmente antes do dia da apresentação.

## Roteiro para apresentar

1. Mostre as responsabilidades separadas: Cliente Web, Gateway, API de tarefas e API de categorias.
2. Cadastre uma conta nova ou entre com uma existente; mostre categorias e tarefas carregadas.
3. Crie uma tarefa e confirme que ela aparece na lista.
4. Abra o Swagger do Gateway e mostre o endpoint de login e o botão `Authorize` para o JWT.
5. Mostre que uma chamada protegida sem token recebe HTTP 401; depois autorize com o token e repita.
6. Explique que o Cliente Web chama o Gateway, o Gateway valida o JWT e encaminha chamadas HTTP às APIs internas; mostre os links HATEOAS nas respostas.
7. Opcionalmente, pare um serviço interno e demonstre a resposta de indisponibilidade do Gateway.

As credenciais e segredos do `.env` são apenas de demonstração. Nunca publique um `.env` real no GitHub.
