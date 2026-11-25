"""Testes dos validadores e dos campos de formulário com máscara."""
import random
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.campos import CampoCEP, CampoCPF, CampoTelefone
from apps.core.utils import formatar_cpf, gerar_cpf
from apps.core.validadores import (
    validar_cep,
    validar_cpf,
    validar_data_nao_futura,
    validar_telefone,
)

CPF_VALIDO = gerar_cpf(random.Random(10))


def test_validar_cpf_aceita_cpf_valido():
    validar_cpf(CPF_VALIDO)
    validar_cpf(formatar_cpf(CPF_VALIDO))


@pytest.mark.parametrize("valor", ["11111111111", "12345678900", "123"])
def test_validar_cpf_recusa_cpf_invalido(valor):
    with pytest.raises(ValidationError):
        validar_cpf(valor)


def test_validar_telefone():
    validar_telefone("11912345678")
    validar_telefone("(11) 4123-4567")
    for invalido in ["912345678", "0191234567", "119123456789"]:
        with pytest.raises(ValidationError):
            validar_telefone(invalido)


def test_validar_cep():
    validar_cep("06750-000")
    with pytest.raises(ValidationError):
        validar_cep("0675")


def test_data_no_futuro_e_recusada():
    validar_data_nao_futura(timezone.localdate())
    with pytest.raises(ValidationError):
        validar_data_nao_futura(timezone.localdate() + timedelta(days=1))


def test_campo_cpf_aceita_mascara_e_devolve_so_numeros():
    assert CampoCPF().clean(formatar_cpf(CPF_VALIDO)) == CPF_VALIDO


def test_campo_cpf_recusa_cpf_invalido():
    with pytest.raises(ValidationError):
        CampoCPF().clean("123.456.789-00")


def test_campos_de_telefone_e_cep_devolvem_so_numeros():
    assert CampoTelefone().clean("(11) 91234-5678") == "11912345678"
    assert CampoCEP().clean("06750-000") == "06750000"
    assert CampoTelefone(required=False).clean("") == ""
