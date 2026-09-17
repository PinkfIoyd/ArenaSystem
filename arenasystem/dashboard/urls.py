from django.urls import path
from . import views, api_views

urlpatterns = [
    # Páginas HTML antigas (mantém para não quebrar /dashboard/)
    path('', views.dashboard, name='dashboard'),
    path('api/receita-mensal/', views.api_receita_mensal, name='api_receita_mensal'),
    path('api/ranking-frequencia/', views.api_ranking_frequencia, name='api_ranking_frequencia'),
    path('api/status-mensalidades/', views.api_status_mensalidades, name='api_status_mensalidades'),
    path('api/ocupacao-quadras/', views.api_ocupacao_quadras, name='api_ocupacao_quadras'),
]

# URLs da API REST do dashboard (sob /api/dashboard/)
api_urlpatterns = [
    path('metricas/', api_views.metricas_gerais, name='api_metricas'),
    path('receita-mensal/', api_views.receita_mensal, name='api_receita_mensal_rest'),
    path('ranking-frequencia/', api_views.ranking_frequencia, name='api_ranking_rest'),
    path('status-mensalidades/', api_views.status_mensalidades, name='api_status_rest'),
    path('ocupacao-quadras/', api_views.ocupacao_quadras, name='api_ocupacao_rest'),
]