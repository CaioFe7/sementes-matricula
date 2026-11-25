from datetime import date

from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.cadastros.forms import ResponsavelForm
from apps.cadastros.models import Crianca
from apps.core.forms import BootstrapFormMixin, HoneypotMixin
from apps.core.utils import calcular_idade

from .models import Atividade, Matricula

# --- Área interna ----------------------------------------------------------


class AtividadeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Atividade
        fields = [
            "nome",
            "descricao",
            "idade_minima",
            "idade_maxima",
            "dias_horarios",
            "vagas",
            "ativa",
        ]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}


class MatriculaForm(BootstrapFormMixin, forms.ModelForm):
    """Matrícula feita pela equipe (por exemplo, com a ficha em papel)."""

    consentimento_lgpd = forms.BooleanField(
        label="O responsável assinou o termo de consentimento",
        error_messages={
            "required": "A matrícula só pode ser registrada com o consentimento do responsável."
        },
    )

    class Meta:
        model = Matricula
        fields = ["crianca", "atividade", "status", "consentimento_lgpd"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["crianca"].queryset = Crianca.objects.order_by("nome")
        self.fields["atividade"].queryset = Atividade.objects.filter(ativa=True)
        self.fields["status"].choices = [
            (Matricula.Status.ATIVA.value, "Ativa (já aprovada)"),
            (Matricula.Status.PENDENTE.value, "Pendente (aguardando aprovação)"),
        ]
        if not self.instance.pk:
            # Matrícula feita pela equipe já nasce aprovada, a não ser que mudem aqui.
            self.initial["status"] = Matricula.Status.ATIVA.value


class MotivoForm(BootstrapFormMixin, forms.Form):
    motivo = forms.CharField(label="Motivo", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["motivo"].classe_coluna = "col-12"


class FiltroMatriculaForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label="Buscar por nome da criança ou protocolo", required=False)
    status = forms.ChoiceField(
        label="Situação", required=False, choices=[("", "Todas"), *Matricula.Status.choices]
    )
    atividade = forms.ModelChoiceField(
        label="Atividade", queryset=Atividade.objects.all(), required=False, empty_label="Todas"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["q"].classe_coluna = "col-12 col-lg-6"
        self.fields["status"].classe_coluna = "col-6 col-lg-3"
        self.fields["atividade"].classe_coluna = "col-6 col-lg-3"

    def filtrar(self, matriculas):
        dados = self.cleaned_data
        busca = dados.get("q", "").strip()
        if busca:
            matriculas = matriculas.filter(
                Q(crianca__nome__icontains=busca) | Q(protocolo__icontains=busca)
            )
        if dados.get("status"):
            matriculas = matriculas.filter(status=dados["status"])
        if dados.get("atividade"):
            matriculas = matriculas.filter(atividade=dados["atividade"])
        return matriculas


# --- Formulário público ----------------------------------------------------


class ResponsavelPublicoForm(HoneypotMixin, ResponsavelForm):
    """Etapa 1 da matrícula on-line.

    Não acusa CPF repetido: se o responsável já tem cadastro, o cadastro
    existente é reaproveitado quando a matrícula é registrada.
    """

    def validate_unique(self):
        pass


class CampoAtividade(forms.ModelChoiceField):
    def label_from_instance(self, atividade):
        return f"{atividade.nome} - {atividade.dias_horarios}"


class EscolhaAtividadesForm(BootstrapFormMixin, forms.Form):
    """Etapa 3: uma atividade para cada criança, conforme a idade."""

    def __init__(self, *args, criancas, hoje=None, **kwargs):
        super().__init__(*args, **kwargs)
        hoje = hoje or timezone.localdate()
        for indice, crianca in enumerate(criancas):
            idade = calcular_idade(date.fromisoformat(crianca["data_nascimento"]), hoje)
            opcoes = Atividade.objects.filter(
                ativa=True, idade_minima__lte=idade, idade_maxima__gte=idade
            )
            campo = CampoAtividade(
                label=f"Atividade para {crianca['nome']} ({idade} anos)",
                queryset=opcoes,
                empty_label="Escolha uma atividade",
                error_messages={"required": "Escolha uma atividade."},
            )
            campo.widget.attrs["class"] = "form-select"
            campo.classe_coluna = "col-12"
            if not opcoes.exists():
                campo.help_text = (
                    "No momento não há atividade disponível para esta idade. Fale com a "
                    "equipe da ONG ou volte e remova esta criança da matrícula."
                )
            self.fields[nome_campo_atividade(indice)] = campo


def nome_campo_atividade(indice: int) -> str:
    return f"atividade_{indice}"


class TermoForm(HoneypotMixin, forms.Form):
    """Etapa 4: consentimento obrigatório do responsável (LGPD)."""

    consentimento = forms.BooleanField(
        label=(
            "Li e concordo com o termo de consentimento e com a política de privacidade, "
            "e declaro ser o pai, a mãe ou o responsável legal."
        ),
        error_messages={
            "required": "Para enviar a matrícula é preciso marcar que você concorda com o termo."
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["consentimento"].widget.attrs["class"] = "form-check-input"
        self.fields["consentimento"].classe_coluna = "col-12"
