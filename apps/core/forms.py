"""Mixins de formulário usados por todos os apps."""
from django import forms
from django.core.exceptions import ValidationError

CAMPO_HONEYPOT = "site"
OPCAO_VAZIA_PADRAO = "---------"
OPCAO_VAZIA = "Selecione"


class BootstrapFormMixin:
    """Aplica as classes do Bootstrap 5 nos campos do formulário."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput | forms.RadioSelect):
                classe = "form-check-input"
            elif isinstance(widget, forms.Select):
                classe = "form-select"
            else:
                classe = "form-control"
            existentes = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existentes} {classe}".strip()
            self._trocar_opcao_vazia(campo)

    @staticmethod
    def _trocar_opcao_vazia(campo):
        """Mostra "Selecione" no lugar dos tracinhos na primeira opção das listas."""
        if isinstance(campo, forms.ModelChoiceField):
            if campo.empty_label == OPCAO_VAZIA_PADRAO:
                campo.empty_label = OPCAO_VAZIA
        elif isinstance(campo, forms.ChoiceField):
            opcoes = list(campo.choices)
            if opcoes and tuple(opcoes[0]) == ("", OPCAO_VAZIA_PADRAO):
                campo.choices = [("", OPCAO_VAZIA), *opcoes[1:]]


class HoneypotMixin:
    """Proteção simples contra robôs.

    Acrescenta um campo escondido por CSS. Pessoas não o veem e o deixam
    vazio; robôs costumam preencher tudo, e nesse caso o envio é recusado.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campo = forms.CharField(
            required=False,
            label="Não preencha este campo",
            widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
        )
        campo.classe_coluna = "campo-extra"
        self.fields[CAMPO_HONEYPOT] = campo

    def clean(self):
        dados = super().clean()
        if dados.get(CAMPO_HONEYPOT):
            raise ValidationError("Não foi possível enviar o formulário. Tente novamente.")
        return dados
