"""Campos de formulário reutilizáveis: CPF, telefone, CEP e data."""
from django import forms

from .utils import somente_digitos
from .validadores import validar_cep, validar_cpf, validar_telefone


class CampoDigitos(forms.CharField):
    """Campo de texto que aceita máscara na tela e guarda só os números."""

    mascara = ""
    exemplo = ""

    def widget_attrs(self, widget):
        atributos = super().widget_attrs(widget)
        atributos.update(
            {
                "data-mascara": self.mascara,
                "inputmode": "numeric",
                "placeholder": self.exemplo,
                "autocomplete": "off",
            }
        )
        return atributos

    def to_python(self, value):
        return somente_digitos(super().to_python(value))


class CampoCPF(CampoDigitos):
    mascara = "cpf"
    exemplo = "000.000.000-00"
    default_validators = [validar_cpf]


class CampoTelefone(CampoDigitos):
    mascara = "telefone"
    exemplo = "(11) 90000-0000"
    default_validators = [validar_telefone]


class CampoCEP(CampoDigitos):
    mascara = "cep"
    exemplo = "00000-000"
    default_validators = [validar_cep]


class CampoData(forms.DateField):
    """Data com o seletor nativo do navegador (aparece como dd/mm/aaaa)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
        kwargs.setdefault("input_formats", ["%Y-%m-%d", "%d/%m/%Y"])
        super().__init__(*args, **kwargs)
