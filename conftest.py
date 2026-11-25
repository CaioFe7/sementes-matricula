"""Fixtures compartilhadas pelos testes. Todos os dados aqui são fictícios."""
import random
from datetime import date

import pytest

from apps.core.utils import gerar_cpf, subtrair_anos

_sorteio = random.Random(2026)


# --- Usuários e perfis -----------------------------------------------------


@pytest.fixture
def perfis(db):
    from apps.contas.perfis import criar_perfis_padrao

    criar_perfis_padrao()


def _criar_usuario(django_user_model, login, perfil):
    from apps.contas.perfis import definir_perfil

    usuario = django_user_model.objects.create_user(username=login)
    definir_perfil(usuario, perfil)
    return usuario


@pytest.fixture
def administrador(perfis, django_user_model):
    from apps.contas.perfis import ADMINISTRADOR

    return _criar_usuario(django_user_model, "admin_teste", ADMINISTRADOR)


@pytest.fixture
def atendente(perfis, django_user_model):
    from apps.contas.perfis import ATENDENTE

    return _criar_usuario(django_user_model, "atendente_teste", ATENDENTE)


@pytest.fixture
def cliente_admin(client, administrador):
    client.force_login(administrador)
    return client


@pytest.fixture
def cliente_atendente(client, atendente):
    client.force_login(atendente)
    return client


# --- Cadastros -------------------------------------------------------------


@pytest.fixture
def bairro(db):
    from apps.cadastros.models import Bairro

    return Bairro.objects.create(nome="Jardim Mirna")


@pytest.fixture
def atividade(db):
    from apps.matriculas.models import Atividade

    return Atividade.objects.create(
        nome="Reforço escolar",
        idade_minima=6,
        idade_maxima=14,
        dias_horarios="Terças e quintas, das 14h às 16h",
        vagas=20,
    )


@pytest.fixture
def criar_responsavel(bairro):
    from apps.cadastros.models import Responsavel

    def _criar(**campos):
        dados = {
            "nome": "Maria Exemplo",
            "cpf": gerar_cpf(_sorteio),
            "data_nascimento": date(1990, 5, 10),
            "parentesco": Responsavel.Parentesco.MAE,
            "telefone": "11912345678",
            "cep": "06750000",
            "logradouro": "Rua Exemplo",
            "numero": "10",
            "bairro": bairro,
        }
        dados.update(campos)
        return Responsavel.objects.create(**dados)

    return _criar


@pytest.fixture
def criar_crianca(bairro, criar_responsavel):
    from django.utils import timezone

    from apps.cadastros.models import Crianca

    def _criar(idade=8, hoje=None, **campos):
        hoje = hoje or timezone.localdate()
        dados = {
            "nome": "Ana Exemplo",
            "data_nascimento": subtrair_anos(hoje, idade),
            "sexo": Crianca.Sexo.FEMININO,
            "bairro": bairro,
        }
        dados.update(campos)
        if "responsavel" not in dados:
            dados["responsavel"] = criar_responsavel()
        return Crianca.objects.create(**dados)

    return _criar


@pytest.fixture
def criar_matricula(atividade, criar_crianca):
    from apps.matriculas.models import Matricula

    def _criar(status=Matricula.Status.ATIVA, **campos):
        dados = {"atividade": atividade, "status": status, "consentimento_lgpd": True}
        dados.update(campos)
        if "crianca" not in dados:
            dados["crianca"] = criar_crianca()
        return Matricula.objects.create(**dados)

    return _criar
