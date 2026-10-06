from django.db import models


class Task(models.Model):
    titulo = models.CharField(max_length=120)
    categoria_id = models.CharField(max_length=50)
    concluida = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo