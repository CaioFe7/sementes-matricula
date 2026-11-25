"""Atividades (turmas) e matrículas."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import ModeloComDatas
from apps.core.utils import gerar_protocolo


class TransicaoInvalida(Exception):
    """A matrícula não está em uma situação que permita a ação pedida."""


class Atividade(models.Model):
    """Atividade ou turma oferecida pela ONG."""

    nome = models.CharField("nome", max_length=100)
    descricao = models.TextField("descrição", blank=True)
    idade_minima = models.PositiveSmallIntegerField("idade mínima")
    idade_maxima = models.PositiveSmallIntegerField("idade máxima")
    dias_horarios = models.CharField(
        "dias e horários", max_length=200, help_text="Ex.: terças e quintas, das 14h às 16h."
    )
    vagas = models.PositiveIntegerField("vagas")
    ativa = models.BooleanField(
        "ativa", default=True, help_text="Atividades inativas não aparecem na matrícula on-line."
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "atividade"
        verbose_name_plural = "atividades"

    def __str__(self):
        return self.nome

    def clean(self):
        if (
            self.idade_minima is not None
            and self.idade_maxima is not None
            and self.idade_minima > self.idade_maxima
        ):
            raise ValidationError(
                {"idade_maxima": "A idade máxima não pode ser menor que a idade mínima."}
            )

    def aceita_idade(self, idade: int) -> bool:
        return self.idade_minima <= idade <= self.idade_maxima

    @property
    def vagas_ocupadas(self) -> int:
        return self.matriculas.filter(status=Matricula.Status.ATIVA).count()


class Matricula(ModeloComDatas):
    """Liga uma criança a uma atividade e guarda o histórico da decisão."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        ATIVA = "ativa", "Ativa"
        RECUSADA = "recusada", "Recusada"
        ENCERRADA = "encerrada", "Encerrada"

    class Origem(models.TextChoices):
        PUBLICO = "publico", "Formulário público"
        INTERNO = "interno", "Cadastro interno"

    # Situações em que a matrícula ainda "ocupa" a criança naquela atividade.
    STATUS_EM_ABERTO = (Status.PENDENTE, Status.ATIVA)

    crianca = models.ForeignKey(
        "cadastros.Crianca",
        verbose_name="criança/adolescente",
        on_delete=models.CASCADE,
        related_name="matriculas",
    )
    atividade = models.ForeignKey(
        Atividade, verbose_name="atividade", on_delete=models.PROTECT, related_name="matriculas"
    )
    protocolo = models.CharField(
        "número de protocolo", max_length=20, unique=True, null=True, blank=True, editable=False
    )
    origem = models.CharField(
        "origem", max_length=10, choices=Origem.choices, default=Origem.INTERNO
    )

    # Situação e decisão
    status = models.CharField(
        "situação", max_length=10, choices=Status.choices, default=Status.PENDENTE
    )
    data_solicitacao = models.DateTimeField("data da solicitação", default=timezone.now)
    data_aprovacao = models.DateTimeField("data da aprovação", null=True, blank=True)
    aprovada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="aprovada por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matriculas_aprovadas",
    )
    motivo = models.TextField("motivo da recusa ou do encerramento", blank=True)
    alterada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="última alteração de situação por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matriculas_alteradas",
    )

    # Consentimento (LGPD)
    consentimento_lgpd = models.BooleanField("consentimento do responsável", default=False)
    data_consentimento = models.DateTimeField("data do consentimento", null=True, blank=True)
    versao_termo = models.CharField("versão do termo aceito", max_length=20, blank=True)

    class Meta:
        ordering = ["-data_solicitacao"]
        verbose_name = "matrícula"
        verbose_name_plural = "matrículas"
        constraints = [
            models.UniqueConstraint(
                fields=["crianca", "atividade"],
                condition=models.Q(status__in=["pendente", "ativa"]),
                name="matricula_unica_em_aberto",
                violation_error_message=(
                    "Esta criança já tem uma matrícula pendente ou ativa nesta atividade."
                ),
            )
        ]

    def __str__(self):
        return f"{self.protocolo or 'sem protocolo'} - {self.crianca} - {self.atividade}"

    def get_absolute_url(self):
        return reverse("matriculas:matricula_detalhe", args=[self.pk])

    def save(self, *args, **kwargs):
        """Salva e, na primeira vez, gera o número de protocolo."""
        super().save(*args, **kwargs)
        if not self.protocolo:
            ano = timezone.localtime(self.data_solicitacao).year
            self.protocolo = gerar_protocolo(ano, self.pk, settings.PREFIXO_PROTOCOLO)
            type(self).objects.filter(pk=self.pk).update(protocolo=self.protocolo)

    # --- Mudanças de situação ----------------------------------------------

    def aprovar(self, usuario):
        """Pendente -> Ativa, registrando quem aprovou e quando."""
        if self.status != self.Status.PENDENTE:
            raise TransicaoInvalida("Só é possível aprovar matrículas pendentes.")
        self.status = self.Status.ATIVA
        self.data_aprovacao = timezone.now()
        self.aprovada_por = usuario
        self.alterada_por = usuario
        self.motivo = ""
        self.save()

    def recusar(self, usuario, motivo: str):
        """Pendente -> Recusada, com motivo."""
        if self.status != self.Status.PENDENTE:
            raise TransicaoInvalida("Só é possível recusar matrículas pendentes.")
        self.status = self.Status.RECUSADA
        self.motivo = motivo
        self.alterada_por = usuario
        self.save()

    def encerrar(self, usuario, motivo: str):
        """Ativa -> Encerrada, com motivo."""
        if self.status != self.Status.ATIVA:
            raise TransicaoInvalida("Só é possível encerrar matrículas ativas.")
        self.status = self.Status.ENCERRADA
        self.motivo = motivo
        self.alterada_por = usuario
        self.save()
