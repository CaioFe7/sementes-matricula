"""Bairros, responsáveis e crianças/adolescentes.

Os campos seguem a lista inicial combinada com a ONG. Quando a ficha de
matrícula oficial chegar, basta acrescentar ou remover campos aqui, ajustar a
lista "fields" do formulário correspondente em forms.py e rodar
"python manage.py makemigrations" e "python manage.py migrate".
"""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import ModeloComDatas
from apps.core.utils import calcular_idade, faixa_etaria
from apps.core.validadores import (
    validar_cep,
    validar_cpf,
    validar_data_nao_futura,
    validar_telefone,
)


class Bairro(models.Model):
    """Lista fixa de bairros, para "Jd. Mirna" e "Jardim Mirna" não virarem dois."""

    nome = models.CharField(
        "nome",
        max_length=100,
        unique=True,
        error_messages={"unique": "Já existe um bairro com este nome."},
    )
    ativo = models.BooleanField(
        "ativo", default=True, help_text="Bairros inativos não aparecem nos formulários."
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "bairro"
        verbose_name_plural = "bairros"

    def __str__(self):
        return self.nome


class Responsavel(ModeloComDatas):
    """Pai, mãe ou responsável legal."""

    class Parentesco(models.TextChoices):
        PAI = "pai", "Pai"
        MAE = "mae", "Mãe"
        AVO = "avo", "Avó/Avô"
        TIO = "tio", "Tio/Tia"
        OUTRO = "outro", "Outro"

    # Identificação
    nome = models.CharField("nome completo", max_length=150)
    cpf = models.CharField(
        "CPF",
        max_length=11,
        unique=True,
        validators=[validar_cpf],
        help_text="Guardado apenas com números.",
        error_messages={"unique": "Já existe um responsável cadastrado com este CPF."},
    )
    data_nascimento = models.DateField("data de nascimento", validators=[validar_data_nao_futura])
    parentesco = models.CharField("parentesco", max_length=10, choices=Parentesco.choices)

    # Contato
    telefone = models.CharField("telefone principal", max_length=11, validators=[validar_telefone])
    telefone_secundario = models.CharField(
        "telefone secundário", max_length=11, blank=True, validators=[validar_telefone]
    )
    email = models.EmailField("e-mail", blank=True)

    # Endereço
    cep = models.CharField("CEP", max_length=8, validators=[validar_cep])
    logradouro = models.CharField("rua, avenida ou travessa", max_length=150)
    numero = models.CharField("número", max_length=10)
    complemento = models.CharField("complemento", max_length=80, blank=True)
    bairro = models.ForeignKey(
        Bairro, verbose_name="bairro", on_delete=models.PROTECT, related_name="responsaveis"
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "responsável"
        verbose_name_plural = "responsáveis"

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("cadastros:responsavel_detalhe", args=[self.pk])


class Crianca(ModeloComDatas):
    """Criança ou adolescente atendido pela ONG."""

    class Sexo(models.TextChoices):
        FEMININO = "F", "Feminino"
        MASCULINO = "M", "Masculino"
        NAO_INFORMADO = "N", "Prefiro não informar"

    # Identificação
    nome = models.CharField("nome completo", max_length=150)
    # Guardamos a data de nascimento, nunca a idade: a idade e a faixa etária
    # são calculadas na hora, então os relatórios não ficam desatualizados.
    data_nascimento = models.DateField("data de nascimento", validators=[validar_data_nao_futura])
    sexo = models.CharField("sexo", max_length=1, choices=Sexo.choices)
    bairro = models.ForeignKey(
        Bairro, verbose_name="bairro", on_delete=models.PROTECT, related_name="criancas"
    )

    # Escola
    escola = models.CharField("escola", max_length=150, blank=True)
    serie = models.CharField("série/ano escolar", max_length=50, blank=True)

    # Saúde
    observacoes_saude = models.TextField(
        "observações de saúde",
        blank=True,
        help_text="Alergias, medicação de uso contínuo, necessidades especiais.",
    )

    # Responsáveis
    responsavel = models.ForeignKey(
        Responsavel,
        verbose_name="responsável principal",
        on_delete=models.PROTECT,
        related_name="criancas",
    )
    outros_responsaveis = models.ManyToManyField(
        Responsavel,
        verbose_name="outros responsáveis",
        blank=True,
        related_name="criancas_secundarias",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "criança/adolescente"
        verbose_name_plural = "crianças e adolescentes"

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("cadastros:crianca_detalhe", args=[self.pk])

    @property
    def idade(self) -> int:
        """Idade em anos completos, calculada na data de hoje."""
        return calcular_idade(self.data_nascimento, timezone.localdate())

    @property
    def faixa_etaria(self) -> str:
        """Faixa etária conforme settings.FAIXAS_ETARIAS."""
        return faixa_etaria(self.idade, settings.FAIXAS_ETARIAS)
