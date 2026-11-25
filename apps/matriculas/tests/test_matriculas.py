"""Testes das regras da matrícula e da fila de aprovação."""
import re

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.matriculas.forms import MatriculaForm
from apps.matriculas.models import Matricula, TransicaoInvalida

pytestmark = pytest.mark.django_db


def test_protocolo_e_gerado_e_nao_se_repete(criar_matricula, criar_crianca):
    primeira = criar_matricula()
    segunda = criar_matricula(crianca=criar_crianca(nome="Outra Criança"))

    assert re.fullmatch(r"SEM-\d{4}-\d{6}", primeira.protocolo)
    assert primeira.protocolo != segunda.protocolo
    primeira.refresh_from_db()
    assert primeira.protocolo


def test_aprovar_registra_quem_aprovou_e_quando(criar_matricula, atendente):
    matricula = criar_matricula(status=Matricula.Status.PENDENTE)

    matricula.aprovar(atendente)

    matricula.refresh_from_db()
    assert matricula.status == Matricula.Status.ATIVA
    assert matricula.aprovada_por == atendente
    assert matricula.data_aprovacao is not None


def test_recusar_e_encerrar_guardam_o_motivo(criar_matricula, criar_crianca, atendente):
    pendente = criar_matricula(status=Matricula.Status.PENDENTE)
    ativa = criar_matricula(crianca=criar_crianca(nome="Outra Criança"))

    pendente.recusar(atendente, "Turma sem vagas")
    ativa.encerrar(atendente, "Mudou de cidade")

    assert pendente.status == Matricula.Status.RECUSADA
    assert pendente.motivo == "Turma sem vagas"
    assert ativa.status == Matricula.Status.ENCERRADA
    assert ativa.alterada_por == atendente


def test_transicoes_invalidas_sao_recusadas(criar_matricula, atendente):
    ativa = criar_matricula(status=Matricula.Status.ATIVA)

    with pytest.raises(TransicaoInvalida):
        ativa.aprovar(atendente)
    with pytest.raises(TransicaoInvalida):
        ativa.recusar(atendente, "motivo")


def test_nao_permite_duas_matriculas_em_aberto_na_mesma_atividade(criar_matricula):
    primeira = criar_matricula(status=Matricula.Status.PENDENTE)
    repetida = Matricula(
        crianca=primeira.crianca, atividade=primeira.atividade, status=Matricula.Status.PENDENTE
    )

    with pytest.raises(ValidationError):
        repetida.full_clean()


def test_matricula_encerrada_permite_nova_matricula(criar_matricula):
    encerrada = criar_matricula(status=Matricula.Status.ENCERRADA)

    nova = criar_matricula(crianca=encerrada.crianca, status=Matricula.Status.PENDENTE)

    assert nova.pk != encerrada.pk


def test_fila_mostra_so_as_pendentes(cliente_atendente, criar_matricula, criar_crianca):
    pendente = criar_matricula(status=Matricula.Status.PENDENTE)
    criar_matricula(crianca=criar_crianca(nome="Outra Criança"), status=Matricula.Status.ATIVA)

    resposta = cliente_atendente.get(reverse("matriculas:matricula_pendentes"))

    assert resposta.status_code == 200
    assert list(resposta.context["matriculas"]) == [pendente]


def test_atendente_aprova_pela_tela(cliente_atendente, atendente, criar_matricula):
    matricula = criar_matricula(status=Matricula.Status.PENDENTE)

    resposta = cliente_atendente.post(reverse("matriculas:matricula_aprovar", args=[matricula.pk]))

    assert resposta.status_code == 302
    matricula.refresh_from_db()
    assert matricula.status == Matricula.Status.ATIVA
    assert matricula.aprovada_por == atendente


def test_aprovar_nao_redireciona_para_outro_site(cliente_atendente, criar_matricula):
    matricula = criar_matricula(status=Matricula.Status.PENDENTE)

    resposta = cliente_atendente.post(
        reverse("matriculas:matricula_aprovar", args=[matricula.pk]),
        {"proxima": "https://site-malicioso.example/"},
    )

    assert resposta.url == matricula.get_absolute_url()


def test_recusar_pela_tela_exige_motivo(cliente_atendente, criar_matricula):
    matricula = criar_matricula(status=Matricula.Status.PENDENTE)
    endereco = reverse("matriculas:matricula_recusar", args=[matricula.pk])

    sem_motivo = cliente_atendente.post(endereco, {"motivo": ""})
    assert sem_motivo.status_code == 200
    matricula.refresh_from_db()
    assert matricula.status == Matricula.Status.PENDENTE

    cliente_atendente.post(endereco, {"motivo": "Fora da faixa etária"})
    matricula.refresh_from_db()
    assert matricula.status == Matricula.Status.RECUSADA


def test_matricula_interna_registra_origem_e_aprovacao(
    cliente_atendente, atendente, criar_crianca, atividade
):
    crianca = criar_crianca()

    resposta = cliente_atendente.post(
        reverse("matriculas:matricula_criar"),
        {
            "crianca": crianca.pk,
            "atividade": atividade.pk,
            "status": "ativa",
            "consentimento_lgpd": "on",
        },
    )

    assert resposta.status_code == 302, resposta.context["form"].errors
    matricula = Matricula.objects.get()
    assert matricula.origem == Matricula.Origem.INTERNO
    assert matricula.aprovada_por == atendente
    assert matricula.data_consentimento is not None


def test_matricula_interna_exige_consentimento(criar_crianca, atividade):
    form = MatriculaForm(
        {"crianca": criar_crianca().pk, "atividade": atividade.pk, "status": "ativa"}
    )

    assert not form.is_valid()
    assert "consentimento_lgpd" in form.errors
