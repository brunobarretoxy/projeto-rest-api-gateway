"""Microserviço responsável por criar e consultar tarefas."""

from itertools import count

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="API de Tarefas",
    description="Serviço interno para criação e consulta de tarefas.",
    version="1.0.0",
)

_task_ids = count(1)
_tasks: list[dict[str, object]] = []


class TaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    category_id: str = Field(min_length=1)


@app.get("/health", tags=["Sistema"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "tasks"}


@app.get("/tasks", tags=["Tarefas"])
async def list_tasks() -> list[dict[str, object]]:
    return _tasks


@app.get("/tasks/{task_id}", tags=["Tarefas"])
async def get_task(task_id: int) -> dict[str, object]:
    for task in _tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Tarefa não encontrada")


@app.post("/tasks", status_code=status.HTTP_201_CREATED, tags=["Tarefas"])
async def create_task(task_input: TaskInput) -> dict[str, object]:
    task: dict[str, object] = {
        "id": next(_task_ids),
        "title": task_input.title,
        "category_id": task_input.category_id,
        "completed": False,
    }
    _tasks.append(task)
    return task
