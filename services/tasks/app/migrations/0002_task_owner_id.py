from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="owner_id",
            field=models.CharField(db_index=True, default="aluno", max_length=32),
        ),
    ]
