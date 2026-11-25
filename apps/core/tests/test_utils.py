"""Testes das funções puras: CPF, idade, faixa etária e formatação."""
import random
from datetime import date, timedelta

import pytest

from apps.core import utils

FAIXAS = [(0, 5), (6, 8), (9, 11), (12, 14), (15, 17)]


# --- CPF -------------------------------------------------------------------


def test_cpf_gerado_e_valido_com_e_sem_mascara():
    cpf = utils.gerar_cpf(random.Random(1))
    assert len(cpf) == 11
    assert utils.cpf_valido(cpf)
    assert utils.cpf_valido(utils.formatar_cpf(cpf))


def test_cpf_com_digito_verificador_errado_e_invalido():
    cpf = utils.gerar_cpf(random.Random(2))
    ultimo_trocado = str((int(cpf[-1]) + 1) % 10)
    assert not utils.cpf_valido(cpf[:-1] + ultimo_trocado)


@pytest.mark.parametrize(
    "valor",
    ["", None, "123", "111.111.111-11", "00000000000", "1234567890123", "abc.def.ghi-jk"],
)
def test_cpf_invalido(valor):
    assert not utils.cpf_valido(valor)


def test_varios_cpfs_gerados_sao_validos():
    sorteio = random.Random(3)
    assert all(utils.cpf_valido(utils.gerar_cpf(sorteio)) for _ in range(200))


# --- Idade -----------------------------------------------------------------


def test_idade_antes_no_dia_e_depois_do_aniversario():
    nascimento = date(2015, 6, 15)
    assert utils.calcular_idade(nascimento, date(2026, 6, 14)) == 10
    assert utils.calcular_idade(nascimento, date(2026, 6, 15)) == 11
    assert utils.calcular_idade(nascimento, date(2026, 6, 16)) == 11


def test_idade_de_quem_nasceu_em_29_de_fevereiro():
    nascimento = date(2012, 2, 29)
    assert utils.calcular_idade(nascimento, date(2025, 2, 28)) == 12
    assert utils.calcular_idade(nascimento, date(2025, 3, 1)) == 13
    assert utils.calcular_idade(nascimento, date(2024, 2, 29)) == 12


def test_idade_de_recem_nascido_e_zero():
    assert utils.calcular_idade(date(2026, 1, 1), date(2026, 12, 31)) == 0


# --- Faixa etária ----------------------------------------------------------


@pytest.mark.parametrize(
    ("idade", "esperado"),
    [
        (0, "0 a 5 anos"),
        (5, "0 a 5 anos"),
        (6, "6 a 8 anos"),
        (8, "6 a 8 anos"),
        (9, "9 a 11 anos"),
        (14, "12 a 14 anos"),
        (17, "15 a 17 anos"),
        (18, utils.FORA_DAS_FAIXAS),
    ],
)
def test_faixa_etaria(idade, esperado):
    assert utils.faixa_etaria(idade, FAIXAS) == esperado


@pytest.mark.parametrize("hoje", [date(2026, 6, 15), date(2024, 2, 29), date(2025, 2, 28)])
def test_intervalo_de_nascimento_combina_com_o_calculo_de_idade(hoje):
    """Quem está dentro do intervalo tem a idade da faixa, e quem está fora não tem."""
    depois_de, ate = utils.intervalo_nascimento(6, 8, hoje)
    nascimento = hoje - timedelta(days=365 * 12)
    while nascimento <= hoje - timedelta(days=365 * 3):
        na_faixa = 6 <= utils.calcular_idade(nascimento, hoje) <= 8
        no_intervalo = depois_de < nascimento <= ate
        assert na_faixa == no_intervalo, nascimento
        nascimento += timedelta(days=1)


# --- Formatação e protocolo ------------------------------------------------


def test_somente_digitos():
    assert utils.somente_digitos("(11) 91234-5678") == "11912345678"
    assert utils.somente_digitos(None) == ""


def test_formatacao():
    assert utils.formatar_cpf("12345678909") == "123.456.789-09"
    assert utils.formatar_telefone("11912345678") == "(11) 91234-5678"
    assert utils.formatar_telefone("1141234567") == "(11) 4123-4567"
    assert utils.formatar_cep("06750000") == "06750-000"
    assert utils.formatar_telefone("") == ""


def test_protocolo():
    assert utils.gerar_protocolo(2026, 123) == "SEM-2026-000123"
    assert utils.gerar_protocolo(2026, 7, "ONG") == "ONG-2026-000007"
