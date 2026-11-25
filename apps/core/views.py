from django.conf import settings
from django.views.generic import TemplateView


class InicioView(TemplateView):
    """Página inicial pública."""

    template_name = "core/inicio.html"


class PrivacidadeView(TemplateView):
    """Política de privacidade e termo de consentimento."""

    template_name = "core/privacidade.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["versao_termo"] = settings.VERSAO_TERMO
        contexto["contato_privacidade"] = settings.CONTATO_PRIVACIDADE
        return contexto
