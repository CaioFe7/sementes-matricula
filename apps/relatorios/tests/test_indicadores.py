"""Testes das contagens do painel de indicadores."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse

from apps.cadastros.models import Bairro, Crianca
from apps.matriculas.models import Atividade, Matricula
from apps.relatorios.servicos import Filtros, linhas_atendidos, montar_relatorio

pytestmark = pytest.mark.django_db

HOJE = date(2026, 6, 15)


@pytest.fixture
def atendidos(criar_crianca, criar_matricula, bairro):
    """Cinco crianças com matrícula ativa e uma com matrícula pendente."""
    centro = Bairro.objects.create(nome="Centro")

    def atendido(idade, sexo, onde, status=Matricula.Status.ATIVA):
        crianca = criar_crianca(
            idade=idade, hoje=HOJE, sexo=sexo, bairro=onde, nome=f"Criança {idade} {sexo}"
        )
        return criar_matricula(crianca=crianca, status=status)

    return [
        atendido(4, Crianca.Sexo.FEMININO, bairro),
        atendido(7, Crianca.Sexo.FEMININO, bairro),
        atendido(7, Crianca.Sexo.MASCULINO, bairro),
        atendido(10, Crianca.Sexo.FEMININO, centro),
        atendido(16, Crianca.Sexo.MASCULINO, centro),
        atendido(12, Crianca.Sexo.MASCULINO, centro, status=Matricula.Status.PENDENTE),
    ]


def test_contagem_por_sexo(atendidos):
    relatorio = montar_relatorio(Filtros(), hoje=HOJE)

    assert relatorio["total"] == 5
    assert relatorio["meninas"] == 3
    assert relatorio["meninos"] == 2
    assert dict(relatorio["por_sexo"]) == {
        "Feminino": 3,
        "Masculino": 2,
        "Prefiro não informar": 0,
    }


def test_contagem_por_faixa_etaria(atendidos):
    relatorio = montar_relatorio(Filtros(), hoje=HOJE)

    assert relatorio["por_faixa"] == [
        ("0 a 5 anos", 1),
        ("6 a 8 anos", 2),
        ("9 a 11 anos", 1),
        ("12 a 14 anos", 0),
        ("15 a 17 anos", 1),
    ]


def test_contagem_por_bairro(atendidos):
    relatorio = montar_relatorio(Filtros(), hoje=HOJE)

    assert relatorio["por_bairro"] == [("Jardim Mirna", 3), ("Centro", 2)]


def test_cartoes_de_ativos_e_pendentes(atendidos):
    relatorio = montar_relatorio(Filtros(), hoje=HOJE)

    assert relatorio["total_ativos"] == 5
    assert relatorio["pendentes"] == 1


def test_filtro_por_situacao(atendidos):
    todas = montar_relatorio(Filtros(status=""), hoje=HOJE)
    pendentes = montar_relatorio(Filtros(status=Matricula.Status.PENDENTE), hoje=HOJE)

    assert todas["total"] == 6
    assert pendentes["total"] == 1
    assert pendentes["meninos"] == 1
    assert dict(pendentes["por_faixa"])["12 a 14 anos"] == 1


def test_filtro_por_periodo(atendidos):
    fuso = ZoneInfo("America/Sao_Paulo")
    antiga = atendidos[0]
    antiga.data_solicitacao = datetime(2026, 1, 10, 12, 0, tzinfo=fuso)
    antiga.save()
    Matricula.objects.exclude(pk=antiga.pk).update(
        data_solicitacao=datetime(2026, 3, 5, 12, 0, tzinfo=fuso)
    )

    desde_fevereiro = montar_relatorio(Filtros(data_inicio=date(2026, 2, 1)), hoje=HOJE)
    ate_janeiro = montar_relatorio(Filtros(data_fim=date(2026, 1, 31)), hoje=HOJE)

    assert desde_fevereiro["total"] == 4
    assert ate_janeiro["total"] == 1


def test_crianca_com_duas_atividades_e_contada_uma_vez(atendidos):
    outra = Atividade.objects.create(
        nome="Capoeira", idade_minima=6, idade_maxima=17, dias_horarios="Sextas", vagas=10
    )
    crianca = atendidos[1].crianca
    Matricula.objects.create(crianca=crianca, atividade=outra, status=Matricula.Status.ATIVA)

    relatorio = montar_relatorio(Filtros(), hoje=HOJE)

    assert relatorio["total"] == 5
    assert relatorio["total_ativos"] == 5
    assert dict(relatorio["por_atividade"]) == {"Reforço escolar": 5, "Capoeira": 1}


def test_linhas_da_planilha(atendidos):
    linhas = linhas_atendidos(Filtros(), hoje=HOJE)

    assert len(linhas) == 5
    assert all(linha[0].startswith("SEM-") for linha in linhas)
    assert {linha[4] for linha in linhas} == {
        "0 a 5 anos",
        "6 a 8 anos",
        "9 a 11 anos",
        "15 a 17 anos",
    }


def test_painel_mostra_os_numeros(cliente_atendente, atendidos):
    resposta = cliente_atendente.get(reverse("relatorios:painel"))

    assert resposta.status_code == 200
    assert resposta.context["relatorio"]["meninas"] == 3
    assert resposta.context["graficos"]["sexo"]["valores"] == [3, 2, 0]


def test_exportacoes_do_administrador(cliente_admin, atendidos):
    excel = cliente_admin.get(reverse("relatorios:exportar_excel"))
    pdf = cliente_admin.get(reverse("relatorios:exportar_pdf") + "?status=")

    assert excel.status_code == 200
    assert "spreadsheetml" in excel["Content-Type"]
    assert excel.content[:2] == b"PK"
    assert pdf.status_code == 200
    assert pdf["Content-Type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")
