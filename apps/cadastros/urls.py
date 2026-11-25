from django.urls import path

from . import views

app_name = "cadastros"

urlpatterns = [
    # Bairros
    path("bairros/", views.BairroListaView.as_view(), name="bairro_lista"),
    path("bairros/novo/", views.BairroCriarView.as_view(), name="bairro_criar"),
    path("bairros/<int:pk>/editar/", views.BairroEditarView.as_view(), name="bairro_editar"),
    # Responsáveis
    path("responsaveis/", views.ResponsavelListaView.as_view(), name="responsavel_lista"),
    path("responsaveis/novo/", views.ResponsavelCriarView.as_view(), name="responsavel_criar"),
    path(
        "responsaveis/<int:pk>/",
        views.ResponsavelDetalheView.as_view(),
        name="responsavel_detalhe",
    ),
    path(
        "responsaveis/<int:pk>/editar/",
        views.ResponsavelEditarView.as_view(),
        name="responsavel_editar",
    ),
    path(
        "responsaveis/<int:pk>/excluir/",
        views.ResponsavelExcluirView.as_view(),
        name="responsavel_excluir",
    ),
    # Crianças e adolescentes
    path("criancas/", views.CriancaListaView.as_view(), name="crianca_lista"),
    path("criancas/nova/", views.CriancaCriarView.as_view(), name="crianca_criar"),
    path("criancas/<int:pk>/", views.CriancaDetalheView.as_view(), name="crianca_detalhe"),
    path("criancas/<int:pk>/editar/", views.CriancaEditarView.as_view(), name="crianca_editar"),
    path("criancas/<int:pk>/excluir/", views.CriancaExcluirView.as_view(), name="crianca_excluir"),
]
