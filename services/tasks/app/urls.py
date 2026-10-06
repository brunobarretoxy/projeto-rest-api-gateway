from django.urls import path

from .views import TaskDetailView, TaskListView


urlpatterns = [
    path("tasks", TaskListView.as_view(), name="task-list"),
    path("tasks/<int:task_id>", TaskDetailView.as_view(), name="task-detail"),
]