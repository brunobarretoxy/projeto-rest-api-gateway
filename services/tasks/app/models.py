from django.db import models


class Task(models.Model):
    owner_id = models.CharField(max_length=32, db_index=True, default="aluno")
    titulo = models.CharField(max_length=120)
    categoria_id = models.CharField(max_length=50)
    concluida = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo