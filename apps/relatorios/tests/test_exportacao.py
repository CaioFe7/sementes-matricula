"""Testes da geração dos arquivos Excel e PDF (não usam o banco)."""
from io import BytesIO

from openpyxl import load_workbook

from apps.relatorios.exportacao import gerar_excel, gerar_pdf

RELATORIO = {
    "total_ativos": 5,
    "pendentes": 1,
    "total": 5,
    "meninas": 3,
    "meninos": 2,
    "por_sexo": [("Feminino", 3), ("Masculino", 2), ("Prefiro não informar", 0)],
    "por_faixa": [("0 a 5 anos", 1), ("6 a 8 anos", 2), ("9 a 11 anos", 2)],
    "por_bairro": [("Jardim Mirna", 3), ("Centro", 2)],
    "por_atividade": [("Reforço escolar", 4), ("Capoeira & Música <turma A>", 1)],
}
CABECALHO = ["Protocolo", "Criança/adolescente", "Idade"]
LINHAS = [["SEM-2026-000001", "Ana Exemplo", 8], ["SEM-2026-000002", "Beto Exemplo", 10]]


def test_excel_tem_resumo_e_lista_de_atendidos():
    conteudo = gerar_excel(
        RELATORIO, CABECALHO, LINHAS, "Relatório de teste", "Situação: Ativa", "15/06/2026"
    )

    pasta = load_workbook(BytesIO(conteudo))
    assert pasta.sheetnames == ["Resumo", "Atendidos"]
    resumo = [[celula.value for celula in linha] for linha in pasta["Resumo"].iter_rows()]
    assert ["Meninas", 3] in resumo
    assert ["Jardim Mirna", 3] in resumo
    atendidos = pasta["Atendidos"]
    assert [celula.value for celula in atendidos[1]] == CABECALHO
    assert atendidos.max_row == 3
    assert atendidos["B2"].value == "Ana Exemplo"


def test_excel_sem_atendidos():
    conteudo = gerar_excel(RELATORIO, CABECALHO, [], "Relatório", "Situação: Ativa", "15/06/2026")

    assert load_workbook(BytesIO(conteudo))["Atendidos"].max_row == 1


def test_pdf_e_gerado_mesmo_com_acentos_e_simbolos():
    conteudo = gerar_pdf(RELATORIO, "Relatório de atendidos - ONG & Cia", "Situação: Ativa", "hoje")

    assert conteudo.startswith(b"%PDF")
    assert len(conteudo) > 1000


def test_pdf_com_relatorio_vazio():
    vazio = {**RELATORIO, "por_bairro": [], "por_atividade": []}

    assert gerar_pdf(vazio, "Relatório", "Situação: Todas", "hoje").startswith(b"%PDF")
