"""Mixins de tela reutilizados pelas views da área interna."""
from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse


class PaginaFormularioMixin:
    """Usa o template genérico de formulário (templates/formulario.html)."""

    template_name = "formulario.html"
    titulo = ""
    descricao = ""
    texto_botao = "Salvar"
    url_voltar = None  # nome da rota para o botão "Cancelar"

    def get_titulo(self):
        return self.titulo

    def get_url_voltar(self):
        return reverse(self.url_voltar) if self.url_voltar else ""

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            titulo=self.get_titulo(),
            descricao=self.descricao,
            texto_botao=self.texto_botao,
            url_voltar=self.get_url_voltar(),
        )
        return contexto


class ExclusaoMixin:
    """Tela de confirmação de exclusão, com aviso quando o registro está em uso."""

    template_name = "confirmar_exclusao.html"
    aviso = ""
    mensagem_sucesso = "Registro excluído."
    mensagem_em_uso = "Este registro não pode ser excluído porque está em uso."
    url_voltar = None

    def get_url_voltar(self):
        if self.url_voltar:
            return reverse(self.url_voltar)
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(aviso=self.aviso, url_voltar=self.get_url_voltar())
        return contexto

    def form_valid(self, form):
        try:
            resposta = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.mensagem_em_uso)
            return redirect(self.get_url_voltar())
        messages.success(self.request, self.mensagem_sucesso)
        return resposta
