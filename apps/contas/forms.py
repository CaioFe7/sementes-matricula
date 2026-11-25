from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordForm,
    UserCreationForm,
)

from apps.core.forms import BootstrapFormMixin

from .perfis import ADMINISTRADOR, ATENDENTE, PERFIS, definir_perfil, perfil_atual

Usuario = get_user_model()

OPCOES_PERFIL = [(nome, nome) for nome in PERFIS]


class EntrarForm(BootstrapFormMixin, AuthenticationForm):
    """Formulário de login."""


class TrocarSenhaForm(BootstrapFormMixin, PasswordChangeForm):
    """Troca da própria senha."""


class DefinirSenhaForm(BootstrapFormMixin, SetPasswordForm):
    """Administrador define uma nova senha para outra pessoa da equipe."""


class UsuarioCriarForm(BootstrapFormMixin, UserCreationForm):
    perfil = forms.ChoiceField(label="Perfil de acesso", choices=OPCOES_PERFIL, initial=ATENDENTE)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        usuario = super().save(commit=True)
        definir_perfil(usuario, self.cleaned_data["perfil"])
        return usuario


class UsuarioEditarForm(BootstrapFormMixin, forms.ModelForm):
    perfil = forms.ChoiceField(label="Perfil de acesso", choices=OPCOES_PERFIL)

    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "email", "is_active")
        labels = {"is_active": "Usuário ativo (pode entrar no sistema)"}

    def __init__(self, *args, usuario_logado=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario_logado = usuario_logado
        self.fields["perfil"].initial = perfil_atual(self.instance) or ATENDENTE

    def clean(self):
        dados = super().clean()
        editando_a_si_mesmo = self.usuario_logado and self.instance.pk == self.usuario_logado.pk
        if editando_a_si_mesmo:
            if not dados.get("is_active") or dados.get("perfil") != ADMINISTRADOR:
                raise forms.ValidationError(
                    "Você não pode desativar o seu próprio usuário nem tirar o seu "
                    "perfil de Administrador. Peça para outro administrador fazer isso."
                )
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=True)
        definir_perfil(usuario, self.cleaned_data["perfil"])
        return usuario
