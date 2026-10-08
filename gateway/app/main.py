"""Gateway público: autentica clientes e encaminha chamadas aos microserviços."""

from datetime import datetime, timedelta, timezone
import os
from typing import Any

import httpx
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

load_dotenv()

from . import user_store

TASKS_API_URL = os.getenv("TASKS_API_URL", "http://127.0.0.1:8001").rstrip("/")
CATEGORIES_API_URL = os.getenv("CATEGORIES_API_URL", "http://127.0.0.1:8002").rstrip("/")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]
JWT_SECRET = os.getenv("JWT_SECRET", "somente-para-desenvolvimento-nao-usar-em-producao")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "aluno")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "projeto123")

app = FastAPI(
    title="Gateway REST — Tarefas",
    description=(
        "Ponto de entrada do cliente web. Valida JWT, encaminha requisições "
        "para os microserviços e apresenta links HATEOAS."
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

bearer = HTTPBearer(
    auto_error=False,
    description="Envie o JWT obtido em /auth/token ou /auth/register como Bearer token.",
)


class DemoCredentials(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class UserRegistration(DemoCredentials):
    """Credentials and contact email used to create a local account."""

    email: str = Field(
        min_length=6,
        max_length=254,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
    )


class TaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    category_id: str = Field(min_length=1)


class TaskCompletionInput(BaseModel):
    completed: bool


async def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    """Valida o bearer token JWT antes de liberar os recursos da API."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT obrigatório",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def gateway_link(href: str, method: str = "GET") -> dict[str, str]:
    return {"href": href, "method": method}


async def call_service(method: str, url: str, **kwargs: Any) -> Any:
    """Executa a chamada interna e converte falhas de rede em erro do Gateway."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", "Erro no microserviço")
        except ValueError:
            detail = "Erro no microserviço"
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Microserviço indisponível; tente novamente em instantes",
        ) from exc


@app.get("/health", tags=["Sistema"])
async def health() -> dict[str, str]:
    """Verifica se o processo do Gateway está ativo (sem autenticação)."""
    return {"status": "ok", "service": "gateway"}


def issue_access_token(username: str) -> dict[str, Any]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": username, "exp": expires_at},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60,
        "user": {"username": username},
        "_links": {
            "tasks": gateway_link("/api/tasks"),
            "categories": gateway_link("/api/categories"),
            "profile": gateway_link("/auth/me"),
        },
    }


@app.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    tags=["Autenticação"],
    responses={409: {"description": "O nome de usuário já está cadastrado."}},
)
async def register(credentials: UserRegistration) -> dict[str, Any]:
    """Cria conta local. Senhas são armazenadas usando scrypt, nunca em texto puro."""
    user_store.ensure_demo_account(DEMO_USERNAME, DEMO_PASSWORD)
    username = credentials.username.strip().lower()
    if not user_store.create_user(username, credentials.email, credentials.password):
        raise HTTPException(
            status_code=409,
            detail="Esse nome de usuário ou e-mail já está cadastrado",
        )
    return issue_access_token(username)


@app.post(
    "/auth/token",
    tags=["Autenticação"],
    responses={401: {"description": "Usuário ou senha incorretos."}},
)
@app.post(
    "/auth/demo-token",
    tags=["Autenticação"],
    deprecated=True,
    include_in_schema=False,
)
async def create_token(credentials: DemoCredentials) -> dict[str, Any]:
    """Autentica uma conta cadastrada e emite JWT. /auth/demo-token é rota legada."""
    user_store.ensure_demo_account(DEMO_USERNAME, DEMO_PASSWORD)
    username = user_store.authenticate_user(credentials.username, credentials.password)
    if username is None:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    return issue_access_token(username)


@app.get("/auth/me", tags=["Autenticação"])
async def current_user(claims: dict[str, Any] = Depends(require_token)) -> dict[str, Any]:
    """Retorna a identidade associada ao JWT apresentado."""
    return {"user": {"username": claims["sub"]}}


@app.get(
    "/api/tasks",
    tags=["Tarefas"],
    responses={401: {"description": "Token Bearer ausente, inválido ou expirado."}},
)
async def list_tasks(claims: dict[str, Any] = Depends(require_token)) -> dict[str, Any]:
    tasks = await call_service(
        "GET",
        f"{TASKS_API_URL}/tasks",
        headers={"X-User-Id": claims["sub"]},
    )
    for task in tasks:
        task["_links"] = {
            "self": gateway_link(f"/api/tasks/{task['id']}"),
            "completion": gateway_link(f"/api/tasks/{task['id']}", "PATCH"),
            "collection": gateway_link("/api/tasks"),
            "category": gateway_link("/api/categories"),
        }
    return {
        "data": tasks,
        "_links": {
            "self": gateway_link("/api/tasks"),
            "create": gateway_link("/api/tasks", "POST"),
            "categories": gateway_link("/api/categories"),
        },
    }


@app.get(
    "/api/tasks/{task_id}",
    tags=["Tarefas"],
    responses={401: {"description": "Token Bearer ausente, inválido ou expirado."}},
)
async def get_task(
    task_id: int,
    claims: dict[str, Any] = Depends(require_token),
) -> dict[str, Any]:
    task = await call_service(
        "GET",
        f"{TASKS_API_URL}/tasks/{task_id}",
        headers={"X-User-Id": claims["sub"]},
    )
    task["_links"] = {
        "self": gateway_link(f"/api/tasks/{task_id}"),
        "completion": gateway_link(f"/api/tasks/{task_id}", "PATCH"),
        "collection": gateway_link("/api/tasks"),
        "category": gateway_link("/api/categories"),
    }
    return {"data": task}


@app.patch(
    "/api/tasks/{task_id}",
    tags=["Tarefas"],
    responses={401: {"description": "Token Bearer ausente, inválido ou expirado."}},
)
async def update_task_completion(
    task_id: int,
    update: TaskCompletionInput,
    claims: dict[str, Any] = Depends(require_token),
) -> dict[str, Any]:
    task = await call_service(
        "PATCH",
        f"{TASKS_API_URL}/tasks/{task_id}",
        json=update.model_dump(),
        headers={"X-User-Id": claims["sub"]},
    )
    task["_links"] = {
        "self": gateway_link(f"/api/tasks/{task_id}"),
        "completion": gateway_link(f"/api/tasks/{task_id}", "PATCH"),
        "collection": gateway_link("/api/tasks"),
        "category": gateway_link("/api/categories"),
    }
    return {"data": task}


@app.post(
    "/api/tasks",
    status_code=status.HTTP_201_CREATED,
    tags=["Tarefas"],
    responses={401: {"description": "Token Bearer ausente, inválido ou expirado."}},
)
async def create_task(
    task_input: TaskInput,
    claims: dict[str, Any] = Depends(require_token),
) -> dict[str, Any]:
    task = await call_service(
        "POST",
        f"{TASKS_API_URL}/tasks",
        json=task_input.model_dump(),
        headers={"X-User-Id": claims["sub"]},
    )
    task["_links"] = {
        "self": gateway_link(f"/api/tasks/{task['id']}"),
        "completion": gateway_link(f"/api/tasks/{task['id']}", "PATCH"),
        "collection": gateway_link("/api/tasks"),
        "category": gateway_link("/api/categories"),
    }
    return {
        "data": task,
        "_links": {"self": gateway_link(f"/api/tasks/{task['id']}")},
    }


@app.get(
    "/api/categories",
    tags=["Categorias"],
    responses={401: {"description": "Token Bearer ausente, inválido ou expirado."}},
)
async def list_categories(_: dict[str, Any] = Depends(require_token)) -> dict[str, Any]:
    categories = await call_service("GET", f"{CATEGORIES_API_URL}/categories")
    for category in categories:
        category["_links"] = {
            "self": gateway_link("/api/categories"),
            "tasks": gateway_link("/api/tasks"),
        }
    return {
        "data": categories,
        "_links": {
            "self": gateway_link("/api/categories"),
            "tasks": gateway_link("/api/tasks"),
        },
    }
