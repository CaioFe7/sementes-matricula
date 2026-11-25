"""Testes dos comandos de management."""
import pytest
from django.contrib.auth.models import Group
from django.core.management import CommandError, call_command

from apps.cadastros.models import Bairro, Crianca, Responsavel
from apps.contas.perfis import PERFIS
from apps.core.utils import cpf_valido
from apps.matriculas.models import Atividade, Matricula


@pytest.mark.django_db
def test_criar_perfis():
    call_command("criar_perfis")
    assert set(Group.objects.values_list("name", flat=True)) >= set(PERFIS)


@pytest.mark.django_db
def test_dados_ficticios_so_rodam_em_desenvolvimento(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("popular_dados_ficticios", quantidade=5)


@pytest.mark.django_db
def test_popular_dados_ficticios():
    pytest.importorskip("faker")
    call_command("popular_dados_ficticios", quantidade=12, semente=1, forcar=True)

    assert Crianca.objects.count() == 12
    assert Bairro.objects.filter(nome="Jardim Mirna").exists()
    assert Atividade.objects.count() >= 5
    assert Matricula.objects.count() == 12
    assert all(cpf_valido(cpf) for cpf in Responsavel.objects.values_list("cpf", flat=True))
    assert not Matricula.objects.filter(protocolo__isnull=True).exists()


@pytest.mark.django_db
def test_criar_admin_teste(django_user_model, settings):
    settings.DEBUG = True
    call_command("criar_admin_teste", usuario="chefe")

    chefe = django_user_model.objects.get(username="chefe")
    assert chefe.is_superuser
    assert chefe.has_usable_password()
    assert django_user_model.objects.filter(username="atendente", is_superuser=False).exists()
