from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.EntrarView.as_view(), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
    path("senha/", views.TrocarSenhaView.as_view(), name="trocar_senha"),
    path("usuarios/", views.UsuarioListaView.as_view(), name="usuario_lista"),
    path("usuarios/novo/", views.UsuarioCriarView.as_view(), name="usuario_criar"),
    path("usuarios/<int:pk>/editar/", views.UsuarioEditarView.as_view(), name="usuario_editar"),
    path("usuarios/<int:pk>/senha/", views.UsuarioSenhaView.as_view(), name="usuario_senha"),
]
