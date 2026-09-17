from django.urls import path
from . import views

urlpatterns = [
    path('minhas-turmas/', views.minhas_turmas, name='minhas_turmas'),
    path('checkin/<int:turma_id>/', views.fazer_checkin, name='fazer_checkin'),
]