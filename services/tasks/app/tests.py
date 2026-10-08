import json

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Task
from .serializers import TaskSerializer


class TaskApiContractTests(APITestCase):
    def test_health_endpoint_reports_service_status(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok", "service": "tasks"})

    def test_api_documentation_exposes_task_routes(self):
        schema_response = self.client.get("/schema?format=json")
        docs_response = self.client.get("/docs")

        self.assertEqual(schema_response.status_code, status.HTTP_200_OK)
        schema = json.loads(schema_response.content)
        self.assertIn("/tasks", schema["paths"])
        self.assertIn("/tasks/{task_id}", schema["paths"])
        self.assertEqual(docs_response.status_code, status.HTTP_200_OK)

    def test_create_task_uses_shared_api_field_names(self):
        response = self.client.post(
            "/tasks",
            {"title": "Estudar REST", "category_id": "estudo"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json(),
            {
                "id": 1,
                "title": "Estudar REST",
                "category_id": "estudo",
                "completed": False,
            },
        )
        self.assertNotIn("titulo", response.json())
        self.assertNotIn("categoria_id", response.json())
        self.assertNotIn("concluida", response.json())

    def test_task_serializer_maps_contract_fields_to_django_model(self):
        serializer = TaskSerializer(
            data={"title": "Mapeamento", "category_id": "estudo"}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        task = serializer.save()
        self.assertEqual(task.titulo, "Mapeamento")
        self.assertEqual(task.categoria_id, "estudo")

    def test_list_and_detail_use_shared_api_field_names(self):
        task = Task.objects.create(
            titulo="Revisar API",
            categoria_id="trabalho",
            concluida=True,
        )

        list_response = self.client.get("/tasks", HTTP_X_USER_ID="aluno")
        detail_response = self.client.get(
            f"/tasks/{task.id}",
            HTTP_X_USER_ID="aluno",
        )
        expected_task = {
            "id": task.id,
            "title": "Revisar API",
            "category_id": "trabalho",
            "completed": True,
        }

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.json(), [expected_task])
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.json(), expected_task)

    def test_tasks_are_isolated_per_gateway_user_header(self):
        self.client.post(
            "/tasks",
            {"title": "Tarefa da conta A", "category_id": "estudo"},
            format="json",
            HTTP_X_USER_ID="conta-a",
        )

        owner_response = self.client.get("/tasks", HTTP_X_USER_ID="conta-a")
        other_user_response = self.client.get("/tasks", HTTP_X_USER_ID="conta-b")

        self.assertEqual(len(owner_response.json()), 1)
        self.assertEqual(other_user_response.json(), [])

    def test_owner_can_mark_task_completed_but_other_user_cannot(self):
        task = Task.objects.create(
            owner_id="conta-a",
            titulo="Concluir trabalho",
            categoria_id="estudo",
        )

        owner_response = self.client.patch(
            f"/tasks/{task.id}",
            {"completed": True},
            format="json",
            HTTP_X_USER_ID="conta-a",
        )
        other_user_response = self.client.patch(
            f"/tasks/{task.id}",
            {"completed": False},
            format="json",
            HTTP_X_USER_ID="conta-b",
        )

        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertTrue(owner_response.json()["completed"])
        self.assertEqual(other_user_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_task_rejects_unknown_category_id(self):
        response = self.client.post(
            "/tasks",
            {"title": "Nova tarefa", "category_id": "inexistente"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category_id", response.json())

    def test_detail_returns_404_for_missing_task(self):
        response = self.client.get("/tasks/999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
