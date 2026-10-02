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

TASKS_API_URL = os.getenv("TASKS_API_URL", "http://127.0.0.1:8001").rstrip("/")
CATEGORIES_API_URL = os.getenv("CATEGORIES_API_URL", "http://127.0.0.1:8002").rstrip("/")
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
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

bearer = HTTPBearer(auto_error=False)


class DemoCredentials(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    category_id: str = Field(min_length=1)


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


@app.post("/auth/demo-token", tags=["Autenticação"])
async def create_demo_token(credentials: DemoCredentials) -> dict[str, Any]:
    """Emite JWT de demonstração. Troque a autenticação simplificada em produção."""
    if credentials.username != DEMO_USERNAME or credentials.password != DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": credentials.username, "exp": expires_at},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60,
        "_links": {
            "tasks": gateway_link("/api/tasks"),
            "categories": gateway_link("/api/categories"),
        },
    }


@app.get("/api/tasks", tags=["Tarefas"])
async def list_tasks(_: dict[str, Any] = Depends(require_token)) -> dict[str, Any]:
    tasks = await call_service("GET", f"{TASKS_API_URL}/tasks")
    for task in tasks:
        task["_links"] = {
            "self": gateway_link(f"/api/tasks/{task['id']}"),
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


@app.get("/api/tasks/{task_id}", tags=["Tarefas"])
async def get_task(task_id: int, _: dict[str, Any] = Depends(require_token)) -> dict[str, Any]:
    task = await call_service("GET", f"{TASKS_API_URL}/tasks/{task_id}")
    task["_links"] = {
        "self": gateway_link(f"/api/tasks/{task_id}"),
        "collection": gateway_link("/api/tasks"),
        "category": gateway_link("/api/categories"),
    }
    return {"data": task}


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED, tags=["Tarefas"])
async def create_task(
    task_input: TaskInput,
    _: dict[str, Any] = Depends(require_token),
) -> dict[str, Any]:
    task = await call_service(
        "POST",
        f"{TASKS_API_URL}/tasks",
        json=task_input.model_dump(),
    )
    task["_links"] = {
        "self": gateway_link(f"/api/tasks/{task['id']}"),
        "collection": gateway_link("/api/tasks"),
        "category": gateway_link("/api/categories"),
    }
    return {
        "data": task,
        "_links": {"self": gateway_link(f"/api/tasks/{task['id']}")},
    }


@app.get("/api/categories", tags=["Categorias"])
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
