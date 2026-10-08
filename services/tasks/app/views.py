from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import Task
from .serializers import TaskSerializer


class TaskCompletionSerializer(serializers.Serializer):
    completed = serializers.BooleanField()


def request_owner_id(request):
    """Read identity forwarded by the private Gateway-to-service connection."""
    return request.headers.get("X-User-Id", "anonymous")[:32]


class TaskListView(APIView):

    @extend_schema(operation_id="tasks_list", responses=TaskSerializer(many=True))
    def get(self, request):
        tarefas = Task.objects.filter(owner_id=request_owner_id(request))

        serializer = TaskSerializer(
            tarefas,
            many=True,
        )

        return Response(serializer.data)

    @extend_schema(
        operation_id="tasks_create",
        request=TaskSerializer,
        responses={201: TaskSerializer, 400: dict},
    )
    def post(self, request):
        serializer = TaskSerializer(
            data=request.data
        )

        if serializer.is_valid():
            tarefa = serializer.save(owner_id=request_owner_id(request))

            return Response(
                TaskSerializer(tarefa).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class TaskDetailView(APIView):

    @extend_schema(
        operation_id="tasks_retrieve",
        responses={200: TaskSerializer, 404: dict},
    )
    def get(self, request, task_id):
        try:
            tarefa = Task.objects.get(
                id=task_id,
                owner_id=request_owner_id(request),
            )

        except Task.DoesNotExist:
            return Response(
                {
                    "detail": "Tarefa não encontrada."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TaskSerializer(tarefa)

        return Response(serializer.data)

    @extend_schema(
        operation_id="tasks_update_completion",
        request=TaskCompletionSerializer,
        responses={200: TaskSerializer, 400: dict, 404: dict},
    )
    def patch(self, request, task_id):
        try:
            tarefa = Task.objects.get(
                id=task_id,
                owner_id=request_owner_id(request),
            )
        except Task.DoesNotExist:
            return Response(
                {"detail": "Tarefa não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TaskCompletionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tarefa.concluida = serializer.validated_data["completed"]
        tarefa.save(update_fields=["concluida"])
        return Response(TaskSerializer(tarefa).data)