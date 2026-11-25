"""Área interna: atividades, matrículas e fila de aprovação."""
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView

from apps.contas.mixins import AdministradorMixin, AreaInternaMixin
from apps.core.mixins import ExclusaoMixin, PaginaFormularioMixin

from .forms import AtividadeForm, FiltroMatriculaForm, MatriculaForm, MotivoForm
from .models import Atividade, Matricula, TransicaoInvalida

ITENS_POR_PAGINA = 20

# --- Atividades (somente Administrador) ------------------------------------


class AtividadeListaView(AdministradorMixin, ListView):
    template_name = "matriculas/atividade_lista.html"
    context_object_name = "atividades"

    def get_queryset(self):
        return Atividade.objects.annotate(
            total_ativas=Count("matriculas", filter=Q(matriculas__status=Matricula.Status.ATIVA)),
            total_pendentes=Count(
                "matriculas", filter=Q(matriculas__status=Matricula.Status.PENDENTE)
            ),
        ).order_by("nome")


class AtividadeCriarView(
    AdministradorMixin, PaginaFormularioMixin, SuccessMessageMixin, CreateView
):
    form_class = AtividadeForm
    titulo = "Nova atividade"
    url_voltar = "matriculas:atividade_lista"
    success_url = reverse_lazy("matriculas:atividade_lista")
    success_message = "Atividade salva."


class AtividadeEditarView(
    AdministradorMixin, PaginaFormularioMixin, SuccessMessageMixin, UpdateView
):
    model = Atividade
    form_class = AtividadeForm
    titulo = "Editar atividade"
    url_voltar = "matriculas:atividade_lista"
    success_url = reverse_lazy("matriculas:atividade_lista")
    success_message = "Atividade salva."


# --- Matrículas ------------------------------------------------------------


class MatriculaListaView(AreaInternaMixin, ListView):
    template_name = "matriculas/matricula_lista.html"
    context_object_name = "matriculas"
    paginate_by = ITENS_POR_PAGINA
    titulo = "Matrículas"
    somente_pendentes = False

    def get_queryset(self):
        matriculas = Matricula.objects.select_related(
            "crianca", "crianca__responsavel", "atividade"
        )
        if self.somente_pendentes:
            # Fila: a solicitação mais antiga aparece primeiro.
            matriculas = matriculas.filter(status=Matricula.Status.PENDENTE).order_by(
                "data_solicitacao"
            )
        self.filtro = FiltroMatriculaForm(self.request.GET or None)
        if self.filtro.is_valid():
            matriculas = self.filtro.filtrar(matriculas)
        return matriculas

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            filtro=self.filtro, titulo=self.titulo, somente_pendentes=self.somente_pendentes
        )
        return contexto


class MatriculaPendentesView(MatriculaListaView):
    """Fila de matrículas aguardando aprovação."""

    titulo = "Matrículas pendentes"
    somente_pendentes = True


class MatriculaDetalheView(AreaInternaMixin, DetailView):
    template_name = "matriculas/matricula_detalhe.html"
    context_object_name = "matricula"
    queryset = Matricula.objects.select_related(
        "crianca", "crianca__responsavel", "crianca__bairro", "atividade", "aprovada_por"
    )


class MatriculaCriarView(AreaInternaMixin, PaginaFormularioMixin, CreateView):
    form_class = MatriculaForm
    titulo = "Nova matrícula"
    descricao = "Use esta tela quando a matrícula for feita presencialmente pela equipe."
    url_voltar = "matriculas:matricula_lista"

    def get_initial(self):
        inicial = super().get_initial()
        crianca = self.request.GET.get("crianca", "")
        if crianca.isdigit():
            inicial["crianca"] = crianca
        return inicial

    def form_valid(self, form):
        matricula = form.save(commit=False)
        agora = timezone.now()
        matricula.origem = Matricula.Origem.INTERNO
        matricula.data_consentimento = agora
        matricula.versao_termo = settings.VERSAO_TERMO
        matricula.alterada_por = self.request.user
        if matricula.status == Matricula.Status.ATIVA:
            matricula.aprovada_por = self.request.user
            matricula.data_aprovacao = agora
        matricula.save()
        self.object = matricula
        messages.success(self.request, f"Matrícula registrada. Protocolo {matricula.protocolo}.")
        return redirect(matricula)


class MatriculaAprovarView(AreaInternaMixin, View):
    """Aprova uma matrícula pendente (somente por POST)."""

    def post(self, request, pk):
        matricula = get_object_or_404(Matricula, pk=pk)
        try:
            matricula.aprovar(request.user)
        except TransicaoInvalida as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, f"Matrícula {matricula.protocolo} aprovada.")
        # "proxima" permite voltar para a fila; só aceitamos endereços do próprio site.
        proxima = request.POST.get("proxima", "")
        if proxima and url_has_allowed_host_and_scheme(
            proxima, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(proxima)
        return redirect(matricula)


class MatriculaDecisaoView(AreaInternaMixin, PaginaFormularioMixin, FormView):
    """Base para recusar ou encerrar uma matrícula, sempre com motivo."""

    form_class = MotivoForm
    acao = ""  # nome do método do model: "recusar" ou "encerrar"
    mensagem_sucesso = ""

    def get_matricula(self):
        if not hasattr(self, "_matricula"):
            self._matricula = get_object_or_404(
                Matricula.objects.select_related("crianca", "atividade"), pk=self.kwargs["pk"]
            )
        return self._matricula

    def get_titulo(self):
        matricula = self.get_matricula()
        return f"{self.titulo}: {matricula.crianca.nome} ({matricula.atividade.nome})"

    def get_url_voltar(self):
        return self.get_matricula().get_absolute_url()

    def form_valid(self, form):
        matricula = self.get_matricula()
        try:
            getattr(matricula, self.acao)(self.request.user, form.cleaned_data["motivo"])
        except TransicaoInvalida as erro:
            messages.error(self.request, str(erro))
        else:
            messages.success(self.request, self.mensagem_sucesso)
        return redirect(matricula)


class MatriculaRecusarView(MatriculaDecisaoView):
    titulo = "Recusar matrícula"
    texto_botao = "Recusar matrícula"
    acao = "recusar"
    mensagem_sucesso = "Matrícula recusada."


class MatriculaEncerrarView(MatriculaDecisaoView):
    titulo = "Encerrar matrícula"
    texto_botao = "Encerrar matrícula"
    acao = "encerrar"
    mensagem_sucesso = "Matrícula encerrada."


class MatriculaExcluirView(AdministradorMixin, ExclusaoMixin, DeleteView):
    model = Matricula
    success_url = reverse_lazy("matriculas:matricula_lista")
    aviso = "Para tirar uma criança de uma atividade, prefira encerrar a matrícula."
    mensagem_sucesso = "Matrícula excluída."
