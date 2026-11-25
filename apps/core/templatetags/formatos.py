"""Filtros de template para exibir CPF, telefone e CEP formatados."""
from django import template

from apps.core import utils

register = template.Library()


@register.filter
def cpf(valor):
    return utils.formatar_cpf(valor)


@register.filter
def telefone(valor):
    return utils.formatar_telefone(valor)


@register.filter
def cep(valor):
    return utils.formatar_cep(valor)
