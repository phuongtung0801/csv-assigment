from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_csv, name='upload_csv'),
    path('operate/', views.perform_operation, name='perform_operation'),
    path('status/', views.task_status, name='task_status'),
]
