"""Regras para gravar a matrícula feita pelo formulário público."""
from datetime import date

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.cadastros.forms import CriancaPublicaForm
from apps.cadastros.models import Crianca, Responsavel
from apps.core.utils import calcular_idade

from .forms import ResponsavelPublicoForm
from .models import Atividade, Matricula


class DadosInvalidos(Exception):
    """Os dados guardados durante as etapas não passaram na conferência final."""


@transaction.atomic
def registrar_matriculas_publicas(dados: dict) -> list[Matricula]:
    """Cria responsável, crianças e matrículas pendentes de uma só vez.

    `dados` é o que foi guardado na sessão durante as etapas:
    {"responsavel": {...}, "criancas": [{...}], "atividades": ["id", ...]}.
    Tudo é validado de novo aqui; se algo falhar, nada é gravado.
    """
    criancas = dados.get("criancas") or []
    atividades = dados.get("atividades") or []
    if not dados.get("responsavel") or not criancas or len(criancas) != len(atividades):
        raise DadosInvalidos("Faltam dados da matrícula.")

    responsavel = _obter_responsavel(dados["responsavel"])
    agora = timezone.now()
    hoje = timezone.localdate()
    matriculas = []
    for dados_crianca, atividade_id in zip(criancas, atividades, strict=True):
        crianca = _obter_crianca(dados_crianca, responsavel)
        atividade = Atividade.objects.filter(pk=atividade_id, ativa=True).first()
        idade = calcular_idade(crianca.data_nascimento, hoje)
        if atividade is None or not atividade.aceita_idade(idade):
            raise DadosInvalidos("A atividade escolhida não está disponível.")
        matriculas.append(_obter_matricula(crianca, atividade, agora))
    return matriculas


def _obter_responsavel(dados: dict) -> Responsavel:
    """Reaproveita o responsável com o mesmo CPF ou cria um novo."""
    form = ResponsavelPublicoForm(data=dados)
    if not form.is_valid():
        raise DadosInvalidos("Os dados do responsável estão incompletos.")
    existente = Responsavel.objects.filter(cpf=form.cleaned_data["cpf"]).first()
    return existente or form.save()


def _obter_crianca(dados: dict, responsavel: Responsavel) -> Crianca:
    """Reaproveita a criança já cadastrada para o responsável ou cria uma nova."""
    form = CriancaPublicaForm(data=dados)
    if not form.is_valid():
        raise DadosInvalidos("Os dados da criança estão incompletos.")
    nascimento: date = form.cleaned_data["data_nascimento"]
    existente = Crianca.objects.filter(
        responsavel=responsavel,
        nome__iexact=form.cleaned_data["nome"],
        data_nascimento=nascimento,
    ).first()
    if existente:
        return existente
    crianca = form.save(commit=False)
    crianca.responsavel = responsavel
    crianca.save()
    return crianca


def _obter_matricula(crianca: Crianca, atividade: Atividade, agora) -> Matricula:
    """Cria a matrícula pendente, sem duplicar uma que já esteja em aberto."""
    em_aberto = Matricula.objects.filter(
        crianca=crianca, atividade=atividade, status__in=Matricula.STATUS_EM_ABERTO
    ).first()
    if em_aberto:
        return em_aberto
    return Matricula.objects.create(
        crianca=crianca,
        atividade=atividade,
        status=Matricula.Status.PENDENTE,
        origem=Matricula.Origem.PUBLICO,
        data_solicitacao=agora,
        consentimento_lgpd=True,
        data_consentimento=agora,
        versao_termo=settings.VERSAO_TERMO,
    )
