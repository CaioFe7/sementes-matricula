from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView

from apps.core.mixins import PaginaFormularioMixin

from .forms import (
    DefinirSenhaForm,
    EntrarForm,
    TrocarSenhaForm,
    UsuarioCriarForm,
    UsuarioEditarForm,
)
from .mixins import AdministradorMixin
from .perfis import perfil_atual

Usuario = get_user_model()


def conferir_permissao_sobre(usuario_logado, usuario_alvo):
    """Só um superusuário pode alterar outro superusuário (ou a senha dele)."""
    if usuario_alvo.is_superuser and not usuario_logado.is_superuser:
        raise PermissionDenied("Somente um superusuário pode alterar este usuário.")


class EntrarView(LoginView):
    template_name = "contas/login.html"
    authentication_form = EntrarForm
    redirect_authenticated_user = True


class TrocarSenhaView(LoginRequiredMixin, PaginaFormularioMixin, PasswordChangeView):
    form_class = TrocarSenhaForm
    titulo = "Trocar minha senha"
    texto_botao = "Trocar senha"
    url_voltar = "relatorios:painel"
    success_url = reverse_lazy("relatorios:painel")

    def form_valid(self, form):
        resposta = super().form_valid(form)
        messages.success(self.request, "Senha alterada.")
        return resposta


class UsuarioListaView(AdministradorMixin, ListView):
    template_name = "contas/usuario_lista.html"
    context_object_name = "usuarios"

    def get_queryset(self):
        usuarios = list(Usuario.objects.order_by("username").prefetch_related("groups"))
        for usuario in usuarios:
            usuario.perfil = perfil_atual(usuario)
        return usuarios


class UsuarioCriarView(AdministradorMixin, PaginaFormularioMixin, SuccessMessageMixin, CreateView):
    form_class = UsuarioCriarForm
    titulo = "Novo usuário da equipe"
    url_voltar = "contas:usuario_lista"
    success_url = reverse_lazy("contas:usuario_lista")
    success_message = "Usuário criado."


class UsuarioEditarView(AdministradorMixin, PaginaFormularioMixin, SuccessMessageMixin, UpdateView):
    model = Usuario
    form_class = UsuarioEditarForm
    url_voltar = "contas:usuario_lista"
    success_url = reverse_lazy("contas:usuario_lista")
    success_message = "Usuário atualizado."

    def get_object(self, queryset=None):
        usuario = super().get_object(queryset)
        conferir_permissao_sobre(self.request.user, usuario)
        return usuario

    def get_titulo(self):
        return f"Editar usuário: {self.object.username}"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario_logado"] = self.request.user
        return kwargs


class UsuarioSenhaView(AdministradorMixin, PaginaFormularioMixin, FormView):
    form_class = DefinirSenhaForm
    texto_botao = "Definir nova senha"
    url_voltar = "contas:usuario_lista"

    def get_usuario(self):
        if not hasattr(self, "_usuario"):
            self._usuario = get_object_or_404(Usuario, pk=self.kwargs["pk"])
            conferir_permissao_sobre(self.request.user, self._usuario)
        return self._usuario

    def get_titulo(self):
        return f"Nova senha para: {self.get_usuario().username}"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.get_usuario()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Senha redefinida.")
        return redirect("contas:usuario_lista")
