from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.contas.mixins import AdministradorMixin, AreaInternaMixin
from apps.core.mixins import ExclusaoMixin, PaginaFormularioMixin

from .forms import (
    BairroForm,
    CriancaForm,
    FiltroCriancaForm,
    FiltroResponsavelForm,
    ResponsavelForm,
)
from .models import Bairro, Crianca, Responsavel

ITENS_POR_PAGINA = 20


class ListaComFiltroMixin:
    """Lista paginada com um formulário de busca e filtros no topo."""

    paginate_by = ITENS_POR_PAGINA
    filtro_class = None

    def get_base_queryset(self):
        raise NotImplementedError

    def get_queryset(self):
        registros = self.get_base_queryset()
        self.filtro = self.filtro_class(self.request.GET or None)
        if self.filtro.is_valid():
            registros = self.filtro.filtrar(registros)
        return registros

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["filtro"] = self.filtro
        return contexto


# --- Bairros (somente Administrador) ---------------------------------------


class BairroListaView(AdministradorMixin, ListView):
    template_name = "cadastros/bairro_lista.html"
    context_object_name = "bairros"

    def get_queryset(self):
        return Bairro.objects.annotate(total_criancas=Count("criancas"))


class BairroCriarView(AdministradorMixin, PaginaFormularioMixin, SuccessMessageMixin, CreateView):
    form_class = BairroForm
    titulo = "Novo bairro"
    url_voltar = "cadastros:bairro_lista"
    success_url = reverse_lazy("cadastros:bairro_lista")
    success_message = "Bairro salvo."


class BairroEditarView(AdministradorMixin, PaginaFormularioMixin, SuccessMessageMixin, UpdateView):
    model = Bairro
    form_class = BairroForm
    titulo = "Editar bairro"
    url_voltar = "cadastros:bairro_lista"
    success_url = reverse_lazy("cadastros:bairro_lista")
    success_message = "Bairro salvo."


# --- Responsáveis ----------------------------------------------------------


class ResponsavelListaView(AreaInternaMixin, ListaComFiltroMixin, ListView):
    template_name = "cadastros/responsavel_lista.html"
    context_object_name = "responsaveis"
    filtro_class = FiltroResponsavelForm

    def get_base_queryset(self):
        return Responsavel.objects.select_related("bairro").annotate(
            total_criancas=Count("criancas")
        )


class ResponsavelDetalheView(AreaInternaMixin, DetailView):
    template_name = "cadastros/responsavel_detalhe.html"
    context_object_name = "responsavel"
    queryset = Responsavel.objects.select_related("bairro")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["criancas"] = self.object.criancas.select_related("bairro")
        contexto["criancas_secundarias"] = self.object.criancas_secundarias.select_related(
            "bairro"
        )
        return contexto


class ResponsavelCriarView(
    AreaInternaMixin, PaginaFormularioMixin, SuccessMessageMixin, CreateView
):
    form_class = ResponsavelForm
    titulo = "Novo responsável"
    url_voltar = "cadastros:responsavel_lista"
    success_message = "Responsável cadastrado."


class ResponsavelEditarView(
    AreaInternaMixin, PaginaFormularioMixin, SuccessMessageMixin, UpdateView
):
    model = Responsavel
    form_class = ResponsavelForm
    titulo = "Editar responsável"
    success_message = "Responsável atualizado."

    def get_url_voltar(self):
        return self.object.get_absolute_url()


class ResponsavelExcluirView(AdministradorMixin, ExclusaoMixin, DeleteView):
    model = Responsavel
    success_url = reverse_lazy("cadastros:responsavel_lista")
    mensagem_sucesso = "Responsável excluído."
    mensagem_em_uso = (
        "Este responsável não pode ser excluído porque é o responsável principal de "
        "uma ou mais crianças. Troque o responsável dessas crianças ou exclua-as antes."
    )


# --- Crianças e adolescentes -----------------------------------------------


class CriancaListaView(AreaInternaMixin, ListaComFiltroMixin, ListView):
    template_name = "cadastros/crianca_lista.html"
    context_object_name = "criancas"
    filtro_class = FiltroCriancaForm

    def get_base_queryset(self):
        return Crianca.objects.select_related("bairro", "responsavel")


class CriancaDetalheView(AreaInternaMixin, DetailView):
    template_name = "cadastros/crianca_detalhe.html"
    context_object_name = "crianca"
    queryset = Crianca.objects.select_related("bairro", "responsavel")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["outros_responsaveis"] = self.object.outros_responsaveis.all()
        contexto["matriculas"] = self.object.matriculas.select_related("atividade", "aprovada_por")
        return contexto


class CriancaCriarView(AreaInternaMixin, PaginaFormularioMixin, SuccessMessageMixin, CreateView):
    form_class = CriancaForm
    titulo = "Nova criança ou adolescente"
    descricao = "O responsável precisa estar cadastrado antes. Depois de salvar, faça a matrícula."
    url_voltar = "cadastros:crianca_lista"
    success_message = "Criança cadastrada."

    def get_initial(self):
        inicial = super().get_initial()
        responsavel = self.request.GET.get("responsavel", "")
        if responsavel.isdigit():
            inicial["responsavel"] = responsavel
        return inicial


class CriancaEditarView(AreaInternaMixin, PaginaFormularioMixin, SuccessMessageMixin, UpdateView):
    model = Crianca
    form_class = CriancaForm
    titulo = "Editar criança ou adolescente"
    success_message = "Cadastro atualizado."

    def get_url_voltar(self):
        return self.object.get_absolute_url()


class CriancaExcluirView(AdministradorMixin, ExclusaoMixin, DeleteView):
    model = Crianca
    success_url = reverse_lazy("cadastros:crianca_lista")
    aviso = "As matrículas desta criança também serão excluídas. Esta ação não pode ser desfeita."
    mensagem_sucesso = "Cadastro excluído."
