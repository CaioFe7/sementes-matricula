from django import forms

from apps.core.campos import CampoData
from apps.core.forms import BootstrapFormMixin
from apps.matriculas.models import Matricula


class FiltroRelatorioForm(BootstrapFormMixin, forms.Form):
    status = forms.ChoiceField(
        label="Situação da matrícula",
        required=False,
        choices=[("", "Todas"), *Matricula.Status.choices],
    )
    data_inicio = CampoData(label="Solicitadas a partir de", required=False)
    data_fim = CampoData(label="Solicitadas até", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.classe_coluna = "col-12 col-sm-4"

    def clean(self):
        dados = super().clean()
        inicio, fim = dados.get("data_inicio"), dados.get("data_fim")
        if inicio and fim and fim < inicio:
            raise forms.ValidationError("A data final não pode ser anterior à data inicial.")
        return dados
