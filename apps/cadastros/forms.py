from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.core.campos import CampoCEP, CampoCPF, CampoData, CampoTelefone
from apps.core.forms import BootstrapFormMixin
from apps.core.utils import (
    calcular_idade,
    chave_faixa,
    intervalo_nascimento,
    rotulo_faixa,
    somente_digitos,
)
from apps.matriculas.models import Atividade, Matricula

from .models import Bairro, Crianca, Responsavel

COLUNA_FILTRO = "col-12 col-sm-6 col-lg-3"


def bairros_disponiveis(instancia=None):
    """Bairros ativos, mais o bairro atual do registro (mesmo que inativo)."""
    condicao = Q(ativo=True)
    if instancia is not None and instancia.bairro_id:
        condicao |= Q(pk=instancia.bairro_id)
    return Bairro.objects.filter(condicao)


class BairroForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Bairro
        fields = ["nome", "ativo"]


class ResponsavelForm(BootstrapFormMixin, forms.ModelForm):
    cpf = CampoCPF(label="CPF")
    data_nascimento = CampoData(label="Data de nascimento")
    telefone = CampoTelefone(label="Telefone principal (com DDD)")
    telefone_secundario = CampoTelefone(label="Telefone secundário (opcional)", required=False)
    cep = CampoCEP(label="CEP")

    class Meta:
        model = Responsavel
        fields = [
            "nome",
            "cpf",
            "data_nascimento",
            "parentesco",
            "telefone",
            "telefone_secundario",
            "email",
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
        ]
        labels = {"email": "E-mail (opcional)", "complemento": "Complemento (opcional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bairro"].queryset = bairros_disponiveis(self.instance)


class CriancaBaseForm(BootstrapFormMixin, forms.ModelForm):
    """Campos da criança comuns ao cadastro interno e ao formulário público."""

    data_nascimento = CampoData(label="Data de nascimento")

    class Meta:
        model = Crianca
        fields = [
            "nome",
            "data_nascimento",
            "sexo",
            "bairro",
            "escola",
            "serie",
            "observacoes_saude",
        ]
        labels = {
            "escola": "Escola (opcional)",
            "serie": "Série/ano escolar (opcional)",
            "observacoes_saude": "Observações de saúde (opcional)",
        }
        widgets = {"observacoes_saude": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bairro"].queryset = bairros_disponiveis(self.instance)
        self.fields["observacoes_saude"].classe_coluna = "col-12"


class CriancaForm(CriancaBaseForm):
    """Cadastro interno, feito pela equipe."""

    class Meta(CriancaBaseForm.Meta):
        fields = CriancaBaseForm.Meta.fields + ["responsavel", "outros_responsaveis"]
        labels = {
            **CriancaBaseForm.Meta.labels,
            "outros_responsaveis": "Outros responsáveis (opcional)",
        }
        help_texts = {
            "outros_responsaveis": "No computador, segure Ctrl para escolher mais de um.",
        }


class CriancaPublicaForm(CriancaBaseForm):
    """Dados da criança no formulário público de matrícula."""

    def clean_data_nascimento(self):
        nascimento = self.cleaned_data["data_nascimento"]
        idade = calcular_idade(nascimento, timezone.localdate())
        if idade > settings.IDADE_MAXIMA_ATENDIMENTO:
            raise forms.ValidationError(
                f"A matrícula on-line é para crianças e adolescentes de até "
                f"{settings.IDADE_MAXIMA_ATENDIMENTO} anos. Confira a data de nascimento."
            )
        return nascimento


class FiltroResponsavelForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label="Buscar por nome ou CPF", required=False)
    bairro = forms.ModelChoiceField(
        label="Bairro", queryset=Bairro.objects.all(), required=False, empty_label="Todos"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.classe_coluna = "col-12 col-sm-6"

    def filtrar(self, responsaveis):
        dados = self.cleaned_data
        busca = dados.get("q", "").strip()
        if busca:
            condicao = Q(nome__icontains=busca)
            numeros = somente_digitos(busca)
            if numeros:
                condicao |= Q(cpf__contains=numeros)
            responsaveis = responsaveis.filter(condicao)
        if dados.get("bairro"):
            responsaveis = responsaveis.filter(bairro=dados["bairro"])
        return responsaveis


class FiltroCriancaForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label="Buscar por nome ou CPF do responsável", required=False)
    bairro = forms.ModelChoiceField(
        label="Bairro", queryset=Bairro.objects.all(), required=False, empty_label="Todos"
    )
    sexo = forms.ChoiceField(
        label="Sexo", required=False, choices=[("", "Todos"), *Crianca.Sexo.choices]
    )
    faixa = forms.ChoiceField(label="Faixa etária", required=False)
    atividade = forms.ModelChoiceField(
        label="Atividade", queryset=Atividade.objects.all(), required=False, empty_label="Todas"
    )
    status = forms.ChoiceField(
        label="Situação da matrícula",
        required=False,
        choices=[("", "Todas"), *Matricula.Status.choices],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["faixa"].choices = [("", "Todas")] + [
            (chave_faixa(minimo, maximo), rotulo_faixa(minimo, maximo))
            for minimo, maximo in settings.FAIXAS_ETARIAS
        ]
        for campo in self.fields.values():
            campo.classe_coluna = COLUNA_FILTRO
        self.fields["q"].classe_coluna = "col-12 col-lg-6"

    def filtrar(self, criancas, hoje=None):
        """Aplica a busca e os filtros escolhidos na lista de crianças."""
        dados = self.cleaned_data
        busca = dados.get("q", "").strip()
        if busca:
            condicao = Q(nome__icontains=busca) | Q(responsavel__nome__icontains=busca)
            numeros = somente_digitos(busca)
            if numeros:
                condicao |= Q(responsavel__cpf__contains=numeros)
            criancas = criancas.filter(condicao)
        if dados.get("bairro"):
            criancas = criancas.filter(bairro=dados["bairro"])
        if dados.get("sexo"):
            criancas = criancas.filter(sexo=dados["sexo"])
        if dados.get("faixa"):
            minimo, maximo = (int(parte) for parte in dados["faixa"].split("-"))
            depois_de, ate = intervalo_nascimento(minimo, maximo, hoje or timezone.localdate())
            criancas = criancas.filter(data_nascimento__gt=depois_de, data_nascimento__lte=ate)
        # Atividade e situação precisam valer para a mesma matrícula,
        # por isso entram juntas no mesmo filter().
        filtros_matricula = {}
        if dados.get("atividade"):
            filtros_matricula["matriculas__atividade"] = dados["atividade"]
        if dados.get("status"):
            filtros_matricula["matriculas__status"] = dados["status"]
        if filtros_matricula:
            criancas = criancas.filter(**filtros_matricula).distinct()
        return criancas
