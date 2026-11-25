"""Matrícula on-line pública, em quatro etapas (sem login).

Os dados de cada etapa ficam guardados na sessão do navegador e só são
gravados no banco no final, depois que o responsável aceita o termo.
"""
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.db import models
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.cadastros.forms import CriancaPublicaForm
from apps.core.forms import CAMPO_HONEYPOT

from .forms import (
    EscolhaAtividadesForm,
    ResponsavelPublicoForm,
    TermoForm,
    nome_campo_atividade,
)
from .models import Atividade
from .servicos import DadosInvalidos, registrar_matriculas_publicas

CHAVE_SESSAO = "matricula_publica"
CHAVE_PROTOCOLOS = "matricula_protocolos"
MAXIMO_CRIANCAS = 10


def _ler(request) -> dict:
    return dict(request.session.get(CHAVE_SESSAO) or {})


def _gravar(request, dados: dict):
    request.session[CHAVE_SESSAO] = dados


def _serializar(form) -> dict:
    """Transforma os dados validados em texto simples, para caber na sessão."""
    dados = {}
    for nome, valor in form.cleaned_data.items():
        if nome == CAMPO_HONEYPOT:
            continue
        if isinstance(valor, date):
            valor = valor.isoformat()
        elif isinstance(valor, models.Model):
            valor = str(valor.pk)
        elif valor is None:
            valor = ""
        dados[nome] = valor
    return dados


def etapa_responsavel(request):
    """Etapa 1: dados do pai, mãe ou responsável."""
    dados = _ler(request)
    form = ResponsavelPublicoForm(request.POST or None, initial=dados.get("responsavel"))
    if request.method == "POST" and form.is_valid():
        dados["responsavel"] = _serializar(form)
        _gravar(request, dados)
        return redirect("matricula_publica:crianca")
    return render(request, "matriculas/publico/responsavel.html", {"form": form, "etapa": 1})


def etapa_crianca(request):
    """Etapa 2: dados da criança. Pode ser repetida para irmãos."""
    dados = _ler(request)
    if not dados.get("responsavel"):
        return redirect("matricula_publica:responsavel")
    criancas = list(dados.get("criancas") or [])

    if request.method == "POST":
        acao = request.POST.get("acao", "continuar")
        formulario_em_branco = not request.POST.get("nome", "").strip()
        if acao == "continuar" and criancas and formulario_em_branco:
            return redirect("matricula_publica:atividade")
        if len(criancas) >= MAXIMO_CRIANCAS:
            messages.error(
                request,
                f"O limite é de {MAXIMO_CRIANCAS} crianças por envio. "
                "Para matricular mais, fale com a equipe da ONG.",
            )
            return redirect("matricula_publica:atividade")
        form = CriancaPublicaForm(request.POST)
        if form.is_valid():
            criancas.append(_serializar(form))
            dados["criancas"] = criancas
            dados.pop("atividades", None)
            _gravar(request, dados)
            if acao == "adicionar":
                messages.success(request, "Criança adicionada. Preencha os dados da próxima.")
                return redirect("matricula_publica:crianca")
            return redirect("matricula_publica:atividade")
    else:
        form = CriancaPublicaForm(initial={"bairro": dados["responsavel"].get("bairro")})

    contexto = {"form": form, "criancas": criancas, "etapa": 2}
    return render(request, "matriculas/publico/crianca.html", contexto)


@require_POST
def remover_crianca(request, indice: int):
    """Tira da lista uma criança adicionada na etapa 2."""
    dados = _ler(request)
    criancas = list(dados.get("criancas") or [])
    if 0 <= indice < len(criancas):
        criancas.pop(indice)
        dados["criancas"] = criancas
        dados.pop("atividades", None)
        _gravar(request, dados)
    return redirect("matricula_publica:crianca")


def etapa_atividade(request):
    """Etapa 3: escolha da atividade de cada criança."""
    dados = _ler(request)
    criancas = dados.get("criancas") or []
    if not dados.get("responsavel"):
        return redirect("matricula_publica:responsavel")
    if not criancas:
        return redirect("matricula_publica:crianca")

    escolhidas = dados.get("atividades") or []
    inicial = {nome_campo_atividade(i): pk for i, pk in enumerate(escolhidas)}
    form = EscolhaAtividadesForm(request.POST or None, criancas=criancas, initial=inicial)
    if request.method == "POST" and form.is_valid():
        dados["atividades"] = [
            str(form.cleaned_data[nome_campo_atividade(i)].pk) for i in range(len(criancas))
        ]
        _gravar(request, dados)
        return redirect("matricula_publica:termo")
    return render(request, "matriculas/publico/atividade.html", {"form": form, "etapa": 3})


def etapa_termo(request):
    """Etapa 4: resumo, termo de consentimento e envio."""
    dados = _ler(request)
    criancas = dados.get("criancas") or []
    escolhidas = dados.get("atividades") or []
    if not dados.get("responsavel"):
        return redirect("matricula_publica:responsavel")
    if not criancas or len(escolhidas) != len(criancas):
        return redirect("matricula_publica:atividade")

    form = TermoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            matriculas = registrar_matriculas_publicas(dados)
        except DadosInvalidos:
            messages.error(
                request,
                "Não foi possível concluir a matrícula. Confira os dados e tente de novo.",
            )
            return redirect("matricula_publica:responsavel")
        request.session.pop(CHAVE_SESSAO, None)
        request.session[CHAVE_PROTOCOLOS] = [
            {
                "protocolo": matricula.protocolo,
                "crianca": matricula.crianca.nome,
                "atividade": matricula.atividade.nome,
            }
            for matricula in matriculas
        ]
        return redirect("matricula_publica:concluida")

    atividades = Atividade.objects.in_bulk([int(pk) for pk in escolhidas if str(pk).isdigit()])
    resumo = [
        {
            "nome": crianca["nome"],
            "atividade": atividades.get(int(pk)) if str(pk).isdigit() else None,
        }
        for crianca, pk in zip(criancas, escolhidas, strict=True)
    ]
    contexto = {
        "form": form,
        "etapa": 4,
        "responsavel": dados["responsavel"],
        "resumo": resumo,
        "versao_termo": settings.VERSAO_TERMO,
    }
    return render(request, "matriculas/publico/termo.html", contexto)


def concluida(request):
    """Tela final com os números de protocolo."""
    protocolos = request.session.get(CHAVE_PROTOCOLOS)
    if not protocolos:
        return redirect("core:inicio")
    return render(request, "matriculas/publico/concluida.html", {"protocolos": protocolos})
