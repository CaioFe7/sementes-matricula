"""Validadores usados nos models e nos formulários."""
from django.core.exceptions import ValidationError
from django.utils import timezone

from .utils import cpf_valido, somente_digitos


def validar_cpf(valor):
    if not cpf_valido(valor):
        raise ValidationError("CPF inválido. Confira os números digitados.", code="cpf_invalido")


def validar_telefone(valor):
    telefone = somente_digitos(valor)
    if len(telefone) not in (10, 11) or telefone[0] == "0":
        raise ValidationError(
            "Telefone inválido. Informe o DDD e o número, por exemplo (11) 91234-5678.",
            code="telefone_invalido",
        )


def validar_cep(valor):
    if len(somente_digitos(valor)) != 8:
        raise ValidationError("CEP inválido. O CEP tem 8 números.", code="cep_invalido")


def validar_data_nao_futura(valor):
    if valor > timezone.localdate():
        raise ValidationError("A data não pode ser no futuro.", code="data_futura")
