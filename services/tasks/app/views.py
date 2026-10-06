from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Task
from .serializers import TaskSerializer


class TaskListView(APIView):

    def get(self, request):
        tarefas = Task.objects.all()

        serializer = TaskSerializer(
            tarefas,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = TaskSerializer(
            data=request.data
        )

        if serializer.is_valid():
            tarefa = serializer.save()

            return Response(
                TaskSerializer(tarefa).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class TaskDetailView(APIView):

    def get(self, request, task_id):
        try:
            tarefa = Task.objects.get(id=task_id)

        except Task.DoesNotExist:
            return Response(
                {
                    "detail": "Tarefa não encontrada."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TaskSerializer(tarefa)

        return Response(serializer.data)