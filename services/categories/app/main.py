"""Microserviço responsável por disponibilizar categorias de tarefas."""

from fastapi import FastAPI

app = FastAPI(
    title="API de Categorias",
    description="Serviço interno que lista as categorias disponíveis.",
    version="1.0.0",
)

_categories = [
    {"id": "estudo", "name": "Estudo"},
    {"id": "trabalho", "name": "Trabalho"},
    {"id": "pessoal", "name": "Pessoal"},
]


@app.get("/health", tags=["Sistema"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "categories"}


@app.get("/categories", tags=["Categorias"])
async def list_categories() -> list[dict[str, str]]:
    return _categories
