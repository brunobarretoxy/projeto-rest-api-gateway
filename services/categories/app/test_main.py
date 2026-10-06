from fastapi.testclient import TestClient

from main import app


client = TestClient(app) # Cria um cliente para fazer requisições à API durante os testes.

 
def test_health(): # Testa se a rota /health está funcionando corretamente.
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "categories",
    }

 
def test_list_categories(): # Testa se a rota /categories retorna todas as categorias com os IDs e nomes definidos no contrato.
    response = client.get("/categories") 

    assert response.status_code == 200

    assert response.json() == [
        {"id": "estudo", "name": "Estudo"},
        {"id": "trabalho", "name": "Trabalho"},
        {"id": "pessoal", "name": "Pessoal"},
        {"id": "projetos", "name": "Projetos"},
        {"id": "exercicio", "name": "Exercício"},
    ]


def test_categories_have_id_and_name(): # Verifica se cada categoria retornada possui os campos  obrigatórios "id" e "name".
    response = client.get("/categories")

    assert response.status_code == 200

    for category in response.json():
        assert "id" in category
        assert "name" in category