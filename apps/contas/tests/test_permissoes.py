"""Testes de login e de permissões dos perfis Administrador e Atendente."""
import pytest
from django.urls import reverse

from apps.cadastros.models import Crianca
from apps.contas.perfis import ADMINISTRADOR, ATENDENTE, eh_administrador, eh_equipe, perfil_atual
from apps.matriculas.models import Matricula

pytestmark = pytest.mark.django_db

ROTAS_INTERNAS = [
    "relatorios:painel",
    "relatorios:exportar_excel",
    "relatorios:exportar_pdf",
    "cadastros:crianca_lista",
    "cadastros:crianca_criar",
    "cadastros:responsavel_lista",
    "cadastros:responsavel_criar",
    "cadastros:bairro_lista",
    "cadastros:bairro_criar",
    "matriculas:matricula_lista",
    "matriculas:matricula_pendentes",
    "matriculas:matricula_criar",
    "matriculas:atividade_lista",
    "matriculas:atividade_criar",
    "contas:usuario_lista",
    "contas:usuario_criar",
    "contas:trocar_senha",
]

ROTAS_SO_DO_ADMINISTRADOR = [
    "relatorios:exportar_excel",
    "relatorios:exportar_pdf",
    "cadastros:bairro_lista",
    "cadastros:bairro_criar",
    "matriculas:atividade_lista",
    "matriculas:atividade_criar",
    "contas:usuario_lista",
    "contas:usuario_criar",
]


def test_perfis(administrador, atendente, django_user_model):
    sem_perfil = django_user_model.objects.create_user(username="sem_perfil")

    assert eh_administrador(administrador) and eh_equipe(administrador)
    assert eh_equipe(atendente) and not eh_administrador(atendente)
    assert not eh_equipe(sem_perfil)
    assert perfil_atual(administrador) == ADMINISTRADOR
    assert perfil_atual(atendente) == ATENDENTE


@pytest.mark.parametrize("rota", ROTAS_INTERNAS)
def test_area_interna_exige_login(client, rota):
    resposta = client.get(reverse(rota))

    assert resposta.status_code == 302
    assert resposta.url.startswith(reverse("contas:login"))


def test_usuario_sem_perfil_nao_entra_na_area_interna(client, django_user_model):
    client.force_login(django_user_model.objects.create_user(username="sem_perfil"))

    assert client.get(reverse("relatorios:painel")).status_code == 403


@pytest.mark.parametrize("rota", ROTAS_INTERNAS)
def test_administrador_abre_todas_as_telas(cliente_admin, criar_matricula, rota):
    criar_matricula()

    assert cliente_admin.get(reverse(rota)).status_code == 200


@pytest.mark.parametrize("rota", sorted(set(ROTAS_INTERNAS) - set(ROTAS_SO_DO_ADMINISTRADOR)))
def test_atendente_abre_as_telas_do_dia_a_dia(cliente_atendente, criar_matricula, rota):
    criar_matricula()

    assert cliente_atendente.get(reverse(rota)).status_code == 200


@pytest.mark.parametrize("rota", ROTAS_SO_DO_ADMINISTRADOR)
def test_atendente_nao_exporta_nem_administra(cliente_atendente, rota):
    assert cliente_atendente.get(reverse(rota)).status_code == 403


def test_atendente_nao_pode_excluir(cliente_atendente, criar_matricula):
    matricula = criar_matricula()
    crianca = matricula.crianca
    rotas = [
        reverse("cadastros:crianca_excluir", args=[crianca.pk]),
        reverse("cadastros:responsavel_excluir", args=[crianca.responsavel.pk]),
        reverse("matriculas:matricula_excluir", args=[matricula.pk]),
    ]

    for rota in rotas:
        assert cliente_atendente.get(rota).status_code == 403
        assert cliente_atendente.post(rota).status_code == 403

    assert Crianca.objects.filter(pk=crianca.pk).exists()
    assert Matricula.objects.filter(pk=matricula.pk).exists()


def test_administrador_pode_excluir(cliente_admin, criar_matricula):
    matricula = criar_matricula()
    crianca = matricula.crianca

    rota = reverse("cadastros:crianca_excluir", args=[crianca.pk])

    assert cliente_admin.get(rota).status_code == 200
    resposta = cliente_admin.post(rota)

    assert resposta.status_code == 302
    assert not Crianca.objects.filter(pk=crianca.pk).exists()
    assert not Matricula.objects.filter(pk=matricula.pk).exists()


def test_responsavel_com_crianca_nao_e_excluido(cliente_admin, criar_crianca):
    crianca = criar_crianca()
    rota = reverse("cadastros:responsavel_excluir", args=[crianca.responsavel.pk])

    resposta = cliente_admin.post(rota)

    assert resposta.status_code == 302
    assert Crianca.objects.filter(pk=crianca.pk).exists()


def test_telas_de_detalhe_e_edicao_abrem(cliente_admin, administrador, criar_matricula):
    matricula = criar_matricula(status=Matricula.Status.PENDENTE)
    crianca = matricula.crianca
    rotas = [
        reverse("cadastros:crianca_detalhe", args=[crianca.pk]),
        reverse("cadastros:crianca_editar", args=[crianca.pk]),
        reverse("cadastros:responsavel_detalhe", args=[crianca.responsavel.pk]),
        reverse("cadastros:responsavel_editar", args=[crianca.responsavel.pk]),
        reverse("cadastros:bairro_editar", args=[crianca.bairro.pk]),
        reverse("matriculas:matricula_detalhe", args=[matricula.pk]),
        reverse("matriculas:matricula_recusar", args=[matricula.pk]),
        reverse("matriculas:matricula_excluir", args=[matricula.pk]),
        reverse("matriculas:atividade_editar", args=[matricula.atividade.pk]),
        reverse("contas:usuario_editar", args=[administrador.pk]),
        reverse("contas:usuario_senha", args=[administrador.pk]),
        reverse("cadastros:crianca_lista") + "?q=ana&faixa=6-8&sexo=F&status=pendente",
        reverse("matriculas:matricula_lista") + "?q=SEM&status=pendente&page=1",
        reverse("relatorios:painel") + "?status=&data_inicio=2026-01-01&data_fim=2026-12-31",
    ]

    for rota in rotas:
        assert cliente_admin.get(rota).status_code == 200, rota


def test_login_com_usuario_e_senha(client, atendente):
    atendente.set_password("uma-senha-so-do-teste")
    atendente.save()

    assert client.get(reverse("contas:login")).status_code == 200
    resposta = client.post(
        reverse("contas:login"),
        {"username": "atendente_teste", "password": "uma-senha-so-do-teste"},
    )

    assert resposta.status_code == 302
    assert resposta.url == reverse("relatorios:painel")


def test_administrador_cria_usuario_com_perfil(cliente_admin, django_user_model):
    senha = "senha-longa-de-teste-2026"
    resposta = cliente_admin.post(
        reverse("contas:usuario_criar"),
        {
            "username": "nova_atendente",
            "first_name": "Nova",
            "last_name": "Atendente",
            "email": "",
            "password1": senha,
            "password2": senha,
            "perfil": ATENDENTE,
        },
    )

    assert resposta.status_code == 302, resposta.context["form"].errors
    novo = django_user_model.objects.get(username="nova_atendente")
    assert perfil_atual(novo) == ATENDENTE
    assert not eh_administrador(novo)


def test_administrador_nao_tira_o_proprio_perfil(cliente_admin, administrador, django_user_model):
    resposta = cliente_admin.post(
        reverse("contas:usuario_editar", args=[administrador.pk]),
        {"first_name": "", "last_name": "", "email": "", "is_active": "on", "perfil": ATENDENTE},
    )

    assert resposta.status_code == 200
    assert resposta.context["form"].non_field_errors()
    do_banco = django_user_model.objects.get(pk=administrador.pk)
    assert perfil_atual(do_banco) == ADMINISTRADOR
