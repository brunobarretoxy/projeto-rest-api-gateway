from rest_framework import serializers

from .categoria_ids import IDS_CATEGORIAS
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "titulo",
            "categoria_id",
            "concluida",
        ]
        read_only_fields = ["id"]

    def validate_titulo(self, valor):
        valor = valor.strip()

        if not valor:
            raise serializers.ValidationError(
                "O título da tarefa não pode ser vazio."
            )

        return valor

    def validate_categoria_id(self, valor):
        if valor not in IDS_CATEGORIAS:
            raise serializers.ValidationError(
                "Categoria inválida."
            )

        return valor