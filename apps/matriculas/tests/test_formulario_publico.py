"""Testes da matrícula on-line pública (as quatro etapas)."""
import random
import re

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.cadastros.models import Crianca, Responsavel
from apps.core.utils import formatar_cpf, gerar_cpf, subtrair_anos
from apps.matriculas.models import Matricula

pytestmark = pytest.mark.django_db

CPF = gerar_cpf(random.Random(42))


def url(nome, *args):
    return reverse(f"matricula_publica:{nome}", args=args)


def dados_responsavel(bairro, **extras):
    dados = {
        "nome": "Maria Exemplo da Silva",
        "cpf": formatar_cpf(CPF),
        "data_nascimento": "1990-05-10",
        "parentesco": "mae",
        "telefone": "(11) 91234-5678",
        "telefone_secundario": "",
        "email": "",
        "cep": "06750-000",
        "logradouro": "Rua Exemplo",
        "numero": "100",
        "complemento": "",
        "bairro": bairro.pk,
        "site": "",
    }
    dados.update(extras)
    return dados


def dados_crianca(bairro, idade=8, **extras):
    dados = {
        "nome": "Ana Exemplo da Silva",
        "data_nascimento": subtrair_anos(timezone.localdate(), idade).isoformat(),
        "sexo": "F",
        "bairro": bairro.pk,
        "escola": "",
        "serie": "",
        "observacoes_saude": "",
        "acao": "continuar",
    }
    dados.update(extras)
    return dados


def preencher_ate_o_termo(client, bairro, atividade):
    """Passa pelas etapas 1, 2 e 3 com dados válidos."""
    resposta = client.post(url("responsavel"), dados_responsavel(bairro))
    assert resposta.status_code == 302, resposta.context["form"].errors
    resposta = client.post(url("crianca"), dados_crianca(bairro))
    assert resposta.status_code == 302, resposta.context["form"].errors
    resposta = client.post(url("atividade"), {"atividade_0": atividade.pk})
    assert resposta.status_code == 302, resposta.context["form"].errors
    assert resposta.url == url("termo")


def test_paginas_publicas_abrem_sem_login(client):
    for endereco in [reverse("core:inicio"), reverse("core:privacidade"), url("responsavel")]:
        assert client.get(endereco).status_code == 200


def test_etapas_seguintes_exigem_as_anteriores(client):
    assert client.get(url("crianca")).url == url("responsavel")
    assert client.get(url("atividade")).url == url("responsavel")
    assert client.get(url("termo")).url == url("responsavel")


def test_consentimento_e_obrigatorio(client, bairro, atividade):
    preencher_ate_o_termo(client, bairro, atividade)

    resposta = client.post(url("termo"), {})

    assert resposta.status_code == 200
    assert "consentimento" in resposta.context["form"].errors
    assert Matricula.objects.count() == 0
    assert Responsavel.objects.count() == 0


def test_matricula_entra_como_pendente_com_protocolo_e_consentimento(client, bairro, atividade):
    preencher_ate_o_termo(client, bairro, atividade)

    resposta = client.post(url("termo"), {"consentimento": "on"})

    assert resposta.status_code == 302
    assert resposta.url == url("concluida")
    matricula = Matricula.objects.get()
    assert matricula.status == Matricula.Status.PENDENTE
    assert matricula.origem == Matricula.Origem.PUBLICO
    assert re.fullmatch(r"SEM-\d{4}-\d{6}", matricula.protocolo)
    assert matricula.consentimento_lgpd is True
    assert matricula.data_consentimento is not None
    assert matricula.versao_termo == settings.VERSAO_TERMO
    assert matricula.aprovada_por is None
    assert matricula.crianca.responsavel.cpf == CPF
    assert matricula.atividade == atividade

    pagina_final = client.get(url("concluida"))
    assert matricula.protocolo in pagina_final.content.decode()


def test_mais_de_uma_crianca_para_o_mesmo_responsavel(client, bairro, atividade):
    client.post(url("responsavel"), dados_responsavel(bairro))
    resposta = client.post(url("crianca"), dados_crianca(bairro, acao="adicionar"))
    assert resposta.url == url("crianca")
    resposta = client.post(
        url("crianca"), dados_crianca(bairro, idade=10, nome="Bruno Exemplo da Silva", sexo="M")
    )
    assert resposta.url == url("atividade")
    client.post(url("atividade"), {"atividade_0": atividade.pk, "atividade_1": atividade.pk})
    client.post(url("termo"), {"consentimento": "on"})

    assert Responsavel.objects.count() == 1
    assert Crianca.objects.count() == 2
    assert Matricula.objects.filter(status=Matricula.Status.PENDENTE).count() == 2
    assert len(set(Matricula.objects.values_list("protocolo", flat=True))) == 2


def test_remover_crianca_da_lista(client, bairro):
    client.post(url("responsavel"), dados_responsavel(bairro))
    client.post(url("crianca"), dados_crianca(bairro, acao="adicionar"))

    client.post(url("remover_crianca", 0))

    assert client.session["matricula_publica"]["criancas"] == []


def test_campo_armadilha_preenchido_bloqueia_o_envio(client, bairro):
    resposta = client.post(url("responsavel"), dados_responsavel(bairro, site="http://spam.example"))

    assert resposta.status_code == 200
    assert resposta.context["form"].non_field_errors()
    assert "matricula_publica" not in client.session


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("cpf", "123.456.789-00"), ("cep", "123"), ("telefone", "1234")],
)
def test_cpf_cep_e_telefone_sao_validados(client, bairro, campo, valor):
    resposta = client.post(url("responsavel"), dados_responsavel(bairro, **{campo: valor}))

    assert resposta.status_code == 200
    assert campo in resposta.context["form"].errors


def test_idade_fora_da_atividade_nao_permite_continuar(client, bairro, atividade):
    """A atividade do teste aceita de 6 a 14 anos; a criança tem 4."""
    client.post(url("responsavel"), dados_responsavel(bairro))
    client.post(url("crianca"), dados_crianca(bairro, idade=4))

    resposta = client.post(url("atividade"), {"atividade_0": atividade.pk})

    assert resposta.status_code == 200
    assert "atividade_0" in resposta.context["form"].errors


def test_maior_de_idade_nao_passa_da_etapa_da_crianca(client, bairro):
    client.post(url("responsavel"), dados_responsavel(bairro))

    resposta = client.post(url("crianca"), dados_crianca(bairro, idade=20))

    assert resposta.status_code == 200
    assert "data_nascimento" in resposta.context["form"].errors


def test_responsavel_ja_cadastrado_e_reaproveitado(client, bairro, atividade, criar_responsavel):
    existente = criar_responsavel(cpf=CPF, nome="Nome Antigo")
    preencher_ate_o_termo(client, bairro, atividade)

    client.post(url("termo"), {"consentimento": "on"})

    assert Responsavel.objects.count() == 1
    assert Matricula.objects.get().crianca.responsavel == existente
