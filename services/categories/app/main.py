"""Microserviço responsável por disponibilizar categorias de tarefas."""

from fastapi import FastAPI 

app = FastAPI(  # Cria a aplicação utilizando o framework FastAPI.
    title="API de Categorias",
    description="Serviço interno que lista as categorias disponíveis.",
    version="1.0.0",
)

_categories = [  # Categorias disponíveis no sistema. O campo "id" utiliza valores string estáveis para que possam ser utilizados também como category_id nas tarefas.
    {"id": "estudo", "name": "Estudo"},
    {"id": "trabalho", "name": "Trabalho"},
    {"id": "pessoal", "name": "Pessoal"},
    {"id": "projetos", "name": "Projetos"},
    {"id": "exercicio", "name": "Exercício"},
]


@app.get("/health", tags=["Sistema"]) # Endpoint utilizado para verificar se o serviço está funcionando. Retorna o status da API e identifica o serviço de categorias.
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "categories"}

 
@app.get("/categories", tags=["Categorias"]) #Endpoint responsável por disponibilizar as categorias. Retorna a lista de categorias contendo seus respectivos IDs e nomes.
async def list_categories() -> list[dict[str, str]]:
    return _categories
