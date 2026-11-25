"""Geração dos arquivos Excel e PDF.

As funções recebem dados prontos (dicionário do relatório e linhas) e
devolvem o conteúdo do arquivo em bytes. Não consultam o banco.
"""
from io import BytesIO
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

VERDE = "146C43"

SECOES = [
    ("Por sexo", "Sexo", "por_sexo"),
    ("Por faixa etária", "Faixa etária", "por_faixa"),
    ("Por bairro", "Bairro", "por_bairro"),
    ("Por atividade (matrículas)", "Atividade", "por_atividade"),
]


def _resumo(relatorio: dict) -> list[tuple[str, int]]:
    return [
        ("Crianças e adolescentes no filtro", relatorio["total"]),
        ("Meninas", relatorio["meninas"]),
        ("Meninos", relatorio["meninos"]),
        ("Atendidos com matrícula ativa (total geral)", relatorio["total_ativos"]),
        ("Matrículas pendentes (total geral)", relatorio["pendentes"]),
    ]


# --- Excel -----------------------------------------------------------------


def _escrever_cabecalho(planilha, linha: int, titulos: list[str]):
    for coluna, titulo in enumerate(titulos, start=1):
        celula = planilha.cell(row=linha, column=coluna, value=titulo)
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = PatternFill("solid", fgColor=VERDE)
        celula.alignment = Alignment(vertical="center", wrap_text=True)


def _ajustar_larguras(planilha, minimo: int = 10, maximo: int = 45):
    larguras = {}
    for linha in planilha.iter_rows():
        for celula in linha:
            if celula.value is not None:
                tamanho = len(str(celula.value)) + 2
                larguras[celula.column] = max(larguras.get(celula.column, 0), tamanho)
    for coluna, largura in larguras.items():
        letra = get_column_letter(coluna)
        planilha.column_dimensions[letra].width = max(minimo, min(largura, maximo))


def gerar_excel(
    relatorio: dict,
    cabecalho: list[str],
    linhas: list[list],
    titulo: str,
    descricao_filtros: str,
    gerado_em: str,
) -> bytes:
    """Planilha com duas abas: "Resumo" (números) e "Atendidos" (lista)."""
    pasta = Workbook()

    resumo = pasta.active
    resumo.title = "Resumo"
    resumo["A1"] = titulo
    resumo["A1"].font = Font(bold=True, size=14)
    resumo["A2"] = descricao_filtros
    resumo["A3"] = f"Gerado em {gerado_em}"

    linha = 5
    _escrever_cabecalho(resumo, linha, ["Indicador", "Total"])
    for rotulo, valor in _resumo(relatorio):
        linha += 1
        resumo.cell(row=linha, column=1, value=rotulo)
        resumo.cell(row=linha, column=2, value=valor)

    for titulo_secao, nome_coluna, chave in SECOES:
        linha += 2
        resumo.cell(row=linha, column=1, value=titulo_secao).font = Font(bold=True)
        linha += 1
        _escrever_cabecalho(resumo, linha, [nome_coluna, "Total"])
        for rotulo, valor in relatorio[chave]:
            linha += 1
            resumo.cell(row=linha, column=1, value=rotulo)
            resumo.cell(row=linha, column=2, value=valor)
    resumo.column_dimensions["A"].width = 48
    resumo.column_dimensions["B"].width = 12

    atendidos = pasta.create_sheet("Atendidos")
    _escrever_cabecalho(atendidos, 1, cabecalho)
    for dados in linhas:
        atendidos.append(dados)
    atendidos.freeze_panes = "A2"
    if linhas:
        ultima_coluna = get_column_letter(len(cabecalho))
        atendidos.auto_filter.ref = f"A1:{ultima_coluna}{len(linhas) + 1}"
    _ajustar_larguras(atendidos)

    saida = BytesIO()
    pasta.save(saida)
    return saida.getvalue()


# --- PDF -------------------------------------------------------------------


def _tabela_pdf(titulos: list[str], linhas: list) -> Table:
    dados = [titulos] + [[str(rotulo), str(valor)] for rotulo, valor in linhas]
    if len(dados) == 1:
        dados.append(["Sem registros", "0"])
    tabela = Table(dados, colWidths=[11 * cm, 3 * cm], repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{VERDE}")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBBBBB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabela


def gerar_pdf(relatorio: dict, titulo: str, descricao_filtros: str, gerado_em: str) -> bytes:
    """PDF só com números (sem dados pessoais), pronto para imprimir."""
    saida = BytesIO()
    documento = SimpleDocTemplate(
        saida,
        pagesize=A4,
        title=titulo,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(escape(titulo), estilos["Title"]),
        Paragraph(escape(descricao_filtros), estilos["Normal"]),
        Paragraph(escape(f"Gerado em {gerado_em}"), estilos["Normal"]),
        Spacer(1, 0.6 * cm),
        Paragraph("Resumo", estilos["Heading2"]),
        _tabela_pdf(["Indicador", "Total"], _resumo(relatorio)),
    ]
    for titulo_secao, nome_coluna, chave in SECOES:
        elementos.append(Spacer(1, 0.5 * cm))
        elementos.append(Paragraph(titulo_secao, estilos["Heading2"]))
        elementos.append(_tabela_pdf([nome_coluna, "Total"], relatorio[chave]))
    documento.build(elementos)
    return saida.getvalue()
