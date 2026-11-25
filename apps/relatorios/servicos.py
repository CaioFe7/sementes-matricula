"""Consultas que alimentam o painel de indicadores e as exportações."""
from collections import Counter
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from apps.cadastros.models import Crianca
from apps.core.utils import (
    FORA_DAS_FAIXAS,
    calcular_idade,
    faixa_etaria,
    formatar_telefone,
    rotulo_faixa,
)
from apps.matriculas.models import Matricula


@dataclass(frozen=True)
class Filtros:
    """Filtros do painel. Situação vazia significa "todas"."""

    status: str = Matricula.Status.ATIVA.value
    data_inicio: date | None = None
    data_fim: date | None = None

    def descricao(self) -> str:
        """Texto dos filtros, usado no cabeçalho dos relatórios exportados."""
        situacao = dict(Matricula.Status.choices).get(self.status, "Todas")
        partes = [f"Situação da matrícula: {situacao}"]
        if self.data_inicio:
            partes.append(f"solicitadas a partir de {self.data_inicio:%d/%m/%Y}")
        if self.data_fim:
            partes.append(f"solicitadas até {self.data_fim:%d/%m/%Y}")
        return ", ".join(partes)


def matriculas_filtradas(filtros: Filtros):
    """Matrículas que atendem à situação e ao período escolhidos."""
    matriculas = Matricula.objects.all()
    if filtros.status:
        matriculas = matriculas.filter(status=filtros.status)
    if filtros.data_inicio:
        matriculas = matriculas.filter(data_solicitacao__date__gte=filtros.data_inicio)
    if filtros.data_fim:
        matriculas = matriculas.filter(data_solicitacao__date__lte=filtros.data_fim)
    return matriculas


def contar_por_faixa(nascimentos, hoje: date) -> list[tuple[str, int]]:
    """Total de crianças em cada faixa etária, na ordem das faixas."""
    faixas = settings.FAIXAS_ETARIAS
    contagem = Counter(faixa_etaria(calcular_idade(nasc, hoje), faixas) for nasc in nascimentos)
    resultado = [
        (rotulo_faixa(minimo, maximo), contagem.get(rotulo_faixa(minimo, maximo), 0))
        for minimo, maximo in faixas
    ]
    if contagem.get(FORA_DAS_FAIXAS):
        resultado.append((FORA_DAS_FAIXAS, contagem[FORA_DAS_FAIXAS]))
    return resultado


def montar_relatorio(filtros: Filtros | None = None, hoje: date | None = None) -> dict:
    """Calcula todos os números do painel.

    Cada criança é contada uma única vez, mesmo que tenha mais de uma
    matrícula dentro do filtro. Só "por atividade" conta matrículas.
    """
    filtros = filtros or Filtros()
    hoje = hoje or timezone.localdate()
    matriculas = matriculas_filtradas(filtros).order_by()
    criancas = Crianca.objects.filter(pk__in=matriculas.values("crianca_id")).order_by()

    por_sexo_bruto = dict(criancas.values_list("sexo").annotate(total=Count("pk")))
    por_sexo = [(rotulo, por_sexo_bruto.get(valor, 0)) for valor, rotulo in Crianca.Sexo.choices]
    por_bairro = list(
        criancas.values_list("bairro__nome")
        .annotate(total=Count("pk"))
        .order_by("-total", "bairro__nome")
    )
    por_atividade = list(
        matriculas.values_list("atividade__nome")
        .annotate(total=Count("pk"))
        .order_by("-total", "atividade__nome")
    )

    return {
        # Cartões fixos (não mudam com os filtros)
        "total_ativos": Crianca.objects.filter(matriculas__status=Matricula.Status.ATIVA)
        .distinct()
        .count(),
        "pendentes": Matricula.objects.filter(status=Matricula.Status.PENDENTE).count(),
        # Números do filtro escolhido
        "total": criancas.count(),
        "meninas": por_sexo_bruto.get(Crianca.Sexo.FEMININO.value, 0),
        "meninos": por_sexo_bruto.get(Crianca.Sexo.MASCULINO.value, 0),
        "por_sexo": por_sexo,
        "por_faixa": contar_por_faixa(criancas.values_list("data_nascimento", flat=True), hoje),
        "por_bairro": por_bairro,
        "por_atividade": por_atividade,
    }


CABECALHO_ATENDIDOS = [
    "Protocolo",
    "Criança/adolescente",
    "Data de nascimento",
    "Idade",
    "Faixa etária",
    "Sexo",
    "Bairro",
    "Escola",
    "Responsável",
    "Telefone",
    "Atividade",
    "Situação",
    "Data da solicitação",
]


def linhas_atendidos(filtros: Filtros, hoje: date | None = None) -> list[list]:
    """Uma linha por matrícula, para a planilha de atendidos."""
    hoje = hoje or timezone.localdate()
    matriculas = (
        matriculas_filtradas(filtros)
        .select_related("crianca", "crianca__bairro", "crianca__responsavel", "atividade")
        .order_by("crianca__nome", "atividade__nome")
    )
    linhas = []
    for matricula in matriculas:
        crianca = matricula.crianca
        idade = calcular_idade(crianca.data_nascimento, hoje)
        linhas.append(
            [
                matricula.protocolo or "",
                crianca.nome,
                crianca.data_nascimento.strftime("%d/%m/%Y"),
                idade,
                faixa_etaria(idade, settings.FAIXAS_ETARIAS),
                crianca.get_sexo_display(),
                crianca.bairro.nome,
                crianca.escola,
                crianca.responsavel.nome,
                formatar_telefone(crianca.responsavel.telefone),
                matricula.atividade.nome,
                matricula.get_status_display(),
                timezone.localtime(matricula.data_solicitacao).strftime("%d/%m/%Y"),
            ]
        )
    return linhas
