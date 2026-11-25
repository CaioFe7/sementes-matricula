"""Testes dos cadastros: idade, faixa etária, filtros e formulário de responsável."""
import random
from datetime import date

import pytest

from apps.cadastros.forms import FiltroCriancaForm, ResponsavelForm
from apps.cadastros.models import Crianca, Responsavel
from apps.core.utils import formatar_cpf, gerar_cpf

pytestmark = pytest.mark.django_db

HOJE = date(2026, 6, 15)


def test_idade_e_faixa_etaria_sao_calculadas_pela_data_de_nascimento(criar_crianca):
    crianca = criar_crianca(idade=7)
    assert crianca.idade == 7
    assert crianca.faixa_etaria == "6 a 8 anos"


def test_o_model_nao_tem_campo_de_idade():
    campos = {campo.name for campo in Crianca._meta.get_fields()}
    assert "data_nascimento" in campos
    assert "idade" not in campos


def test_filtro_por_faixa_etaria(criar_crianca):
    criar_crianca(idade=5, hoje=HOJE, nome="Cinco Anos")
    sete = criar_crianca(idade=7, hoje=HOJE, nome="Sete Anos")
    criar_crianca(idade=12, hoje=HOJE, nome="Doze Anos")

    filtro = FiltroCriancaForm({"faixa": "6-8"})
    assert filtro.is_valid(), filtro.errors
    assert list(filtro.filtrar(Crianca.objects.all(), hoje=HOJE)) == [sete]


def test_filtro_por_nome_cpf_bairro_sexo_e_situacao(criar_crianca, criar_matricula, bairro):
    ana = criar_crianca(nome="Ana Souza", sexo=Crianca.Sexo.FEMININO)
    beto = criar_crianca(nome="Beto Lima", sexo=Crianca.Sexo.MASCULINO)
    criar_matricula(crianca=ana, status="ativa")
    criar_matricula(crianca=beto, status="pendente")

    def buscar(**dados):
        filtro = FiltroCriancaForm(dados)
        assert filtro.is_valid(), filtro.errors
        return set(filtro.filtrar(Crianca.objects.all()))

    assert buscar(q="ana") == {ana}
    assert buscar(q=formatar_cpf(beto.responsavel.cpf)) == {beto}
    assert buscar(sexo="M") == {beto}
    assert buscar(status="ativa") == {ana}
    assert buscar(bairro=bairro.pk) == {ana, beto}


def _dados_responsavel(bairro, cpf):
    return {
        "nome": "Carla Exemplo",
        "cpf": cpf,
        "data_nascimento": "1988-03-20",
        "parentesco": "mae",
        "telefone": "(11) 91234-5678",
        "telefone_secundario": "",
        "email": "",
        "cep": "06750-000",
        "logradouro": "Rua Exemplo",
        "numero": "25",
        "complemento": "",
        "bairro": bairro.pk,
    }


def test_formulario_de_responsavel_guarda_so_os_numeros(bairro):
    cpf = gerar_cpf(random.Random(21))
    form = ResponsavelForm(_dados_responsavel(bairro, formatar_cpf(cpf)))
    assert form.is_valid(), form.errors

    responsavel = form.save()
    assert responsavel.cpf == cpf
    assert responsavel.telefone == "11912345678"
    assert responsavel.cep == "06750000"


def test_formulario_de_responsavel_recusa_cpf_invalido(bairro):
    form = ResponsavelForm(_dados_responsavel(bairro, "123.456.789-00"))
    assert not form.is_valid()
    assert "cpf" in form.errors


def test_formulario_de_responsavel_recusa_cpf_repetido(bairro, criar_responsavel):
    existente = criar_responsavel()
    form = ResponsavelForm(_dados_responsavel(bairro, existente.cpf))
    assert not form.is_valid()
    assert "cpf" in form.errors
    assert Responsavel.objects.count() == 1
