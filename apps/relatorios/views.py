from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.contas.mixins import AdministradorMixin, AreaInternaMixin
from apps.matriculas.models import Matricula

from .exportacao import gerar_excel, gerar_pdf
from .forms import FiltroRelatorioForm
from .servicos import CABECALHO_ATENDIDOS, Filtros, linhas_atendidos, montar_relatorio

TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def ler_filtros(request):
    """Lê os filtros da URL. Sem filtros, mostra as matrículas ativas."""
    if not request.GET:
        form = FiltroRelatorioForm(initial={"status": Matricula.Status.ATIVA.value})
        return form, Filtros()
    form = FiltroRelatorioForm(request.GET)
    if not form.is_valid():
        return form, Filtros()
    dados = form.cleaned_data
    filtros = Filtros(
        status=dados["status"], data_inicio=dados["data_inicio"], data_fim=dados["data_fim"]
    )
    return form, filtros


def _titulo_relatorio() -> str:
    return f"Relatório de atendidos - {settings.NOME_ONG}"


def _agora_formatado() -> str:
    agora = timezone.localtime()
    return f"{agora:%d/%m/%Y} às {agora:%H:%M}"


class PainelView(AreaInternaMixin, TemplateView):
    """Painel de indicadores com cartões e gráficos."""

    template_name = "relatorios/painel.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        form, filtros = ler_filtros(self.request)
        relatorio = montar_relatorio(filtros)
        graficos = {
            chave: {
                "rotulos": [rotulo for rotulo, _ in relatorio[f"por_{chave}"]],
                "valores": [valor for _, valor in relatorio[f"por_{chave}"]],
            }
            for chave in ("sexo", "faixa", "bairro", "atividade")
        }
        contexto.update(
            filtro=form,
            relatorio=relatorio,
            graficos=graficos,
            descricao_filtros=filtros.descricao(),
        )
        return contexto


class ExportarExcelView(AdministradorMixin, View):
    """Planilha com o resumo e a lista de atendidos (somente Administrador)."""

    def get(self, request):
        _, filtros = ler_filtros(request)
        conteudo = gerar_excel(
            relatorio=montar_relatorio(filtros),
            cabecalho=CABECALHO_ATENDIDOS,
            linhas=linhas_atendidos(filtros),
            titulo=_titulo_relatorio(),
            descricao_filtros=filtros.descricao(),
            gerado_em=_agora_formatado(),
        )
        resposta = HttpResponse(conteudo, content_type=TIPO_EXCEL)
        nome = f"relatorio-atendidos-{timezone.localdate():%Y-%m-%d}.xlsx"
        resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
        return resposta


class ExportarPDFView(AdministradorMixin, View):
    """PDF com os números do painel (somente Administrador)."""

    def get(self, request):
        _, filtros = ler_filtros(request)
        conteudo = gerar_pdf(
            relatorio=montar_relatorio(filtros),
            titulo=_titulo_relatorio(),
            descricao_filtros=filtros.descricao(),
            gerado_em=_agora_formatado(),
        )
        resposta = HttpResponse(conteudo, content_type="application/pdf")
        nome = f"relatorio-atendidos-{timezone.localdate():%Y-%m-%d}.pdf"
        resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
        return resposta
