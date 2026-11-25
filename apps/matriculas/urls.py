from django.urls import path

from . import views

app_name = "matriculas"

urlpatterns = [
    # Atividades
    path("atividades/", views.AtividadeListaView.as_view(), name="atividade_lista"),
    path("atividades/nova/", views.AtividadeCriarView.as_view(), name="atividade_criar"),
    path(
        "atividades/<int:pk>/editar/",
        views.AtividadeEditarView.as_view(),
        name="atividade_editar",
    ),
    # Matrículas
    path("matriculas/", views.MatriculaListaView.as_view(), name="matricula_lista"),
    path(
        "matriculas/pendentes/",
        views.MatriculaPendentesView.as_view(),
        name="matricula_pendentes",
    ),
    path("matriculas/nova/", views.MatriculaCriarView.as_view(), name="matricula_criar"),
    path("matriculas/<int:pk>/", views.MatriculaDetalheView.as_view(), name="matricula_detalhe"),
    path(
        "matriculas/<int:pk>/aprovar/",
        views.MatriculaAprovarView.as_view(),
        name="matricula_aprovar",
    ),
    path(
        "matriculas/<int:pk>/recusar/",
        views.MatriculaRecusarView.as_view(),
        name="matricula_recusar",
    ),
    path(
        "matriculas/<int:pk>/encerrar/",
        views.MatriculaEncerrarView.as_view(),
        name="matricula_encerrar",
    ),
    path(
        "matriculas/<int:pk>/excluir/",
        views.MatriculaExcluirView.as_view(),
        name="matricula_excluir",
    ),
]
