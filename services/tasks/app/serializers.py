from rest_framework import serializers

from .categoria_ids import IDS_CATEGORIAS
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    # Public API names follow the shared contract; source maps them to the
    # existing Portuguese field names in the Django model/database.
    title = serializers.CharField(source="titulo", max_length=120)
    category_id = serializers.CharField(source="categoria_id", max_length=50)
    completed = serializers.BooleanField(source="concluida", required=False)

    class Meta:
        model = Task
        fields = ["id", "title", "category_id", "completed"]
        read_only_fields = ["id"]

    def validate_title(self, valor):
        valor = valor.strip()

        if not valor:
            raise serializers.ValidationError(
                "O título da tarefa não pode ser vazio."
            )

        return valor

    def validate_category_id(self, valor):
        if valor not in IDS_CATEGORIAS:
            raise serializers.ValidationError(
                "Categoria inválida."
            )

        return valor