"""Controle de acesso das views.

Quem não está logado é enviado para a tela de login. Quem está logado mas
não tem o perfil necessário recebe a página de acesso negado (erro 403).
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .perfis import eh_administrador, eh_equipe


class AreaInternaMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige login e um dos perfis da equipe (Administrador ou Atendente)."""

    def test_func(self):
        return eh_equipe(self.request.user)


class AdministradorMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige login e o perfil Administrador."""

    def test_func(self):
        return eh_administrador(self.request.user)
