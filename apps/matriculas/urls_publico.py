from django.urls import path

from . import views_publico as views

app_name = "matricula_publica"

urlpatterns = [
    path("", views.etapa_responsavel, name="responsavel"),
    path("crianca/", views.etapa_crianca, name="crianca"),
    path("crianca/<int:indice>/remover/", views.remover_crianca, name="remover_crianca"),
    path("atividade/", views.etapa_atividade, name="atividade"),
    path("termo/", views.etapa_termo, name="termo"),
    path("concluida/", views.concluida, name="concluida"),
]
