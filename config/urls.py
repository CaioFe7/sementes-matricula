"""Rotas principais do projeto."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
    path("conta/", include("apps.contas.urls")),
    path("matricula/", include("apps.matriculas.urls_publico")),
    path("equipe/", include("apps.relatorios.urls")),
    path("equipe/", include("apps.cadastros.urls")),
    path("equipe/", include("apps.matriculas.urls")),
]
