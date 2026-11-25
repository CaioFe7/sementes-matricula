"""Funções puras (sem banco de dados) usadas em todo o sistema.

Ficam aqui o cálculo de idade e faixa etária, a validação de CPF e a
formatação de CPF, telefone e CEP. Por não dependerem do Django, são fáceis
de testar.
"""
import re
from datetime import date

FORA_DAS_FAIXAS = "Fora das faixas"


def somente_digitos(valor) -> str:
    """Remove tudo o que não for número. Ex.: '123.456.789-09' -> '12345678909'."""
    return re.sub(r"\D", "", str(valor or ""))


# --- CPF -------------------------------------------------------------------


def _digito_verificador(numeros: list[int]) -> int:
    peso_inicial = len(numeros) + 1
    soma = sum(numero * (peso_inicial - posicao) for posicao, numero in enumerate(numeros))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto


def cpf_valido(cpf) -> bool:
    """Confere o tamanho e os dois dígitos verificadores do CPF."""
    cpf = somente_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    numeros = [int(caractere) for caractere in cpf]
    return numeros[9] == _digito_verificador(numeros[:9]) and numeros[10] == _digito_verificador(
        numeros[:10]
    )


def gerar_cpf(gerador) -> str:
    """Gera um CPF fictício válido (só números). `gerador` é um random.Random."""
    while True:
        numeros = [gerador.randint(0, 9) for _ in range(9)]
        if len(set(numeros)) > 1:
            break
    numeros.append(_digito_verificador(numeros))
    numeros.append(_digito_verificador(numeros))
    return "".join(str(numero) for numero in numeros)


# --- Formatação ------------------------------------------------------------


def formatar_cpf(valor) -> str:
    cpf = somente_digitos(valor)
    if len(cpf) != 11:
        return str(valor or "")
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def formatar_telefone(valor) -> str:
    telefone = somente_digitos(valor)
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    if len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    return str(valor or "")


def formatar_cep(valor) -> str:
    cep = somente_digitos(valor)
    if len(cep) != 8:
        return str(valor or "")
    return f"{cep[:5]}-{cep[5:]}"


# --- Idade e faixa etária --------------------------------------------------


def calcular_idade(nascimento: date, hoje: date | None = None) -> int:
    """Idade em anos completos na data `hoje`."""
    hoje = hoje or date.today()
    ainda_nao_fez_aniversario = (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
    return hoje.year - nascimento.year - int(ainda_nao_fez_aniversario)


def rotulo_faixa(minimo: int, maximo: int) -> str:
    return f"{minimo} a {maximo} anos"


def chave_faixa(minimo: int, maximo: int) -> str:
    return f"{minimo}-{maximo}"


def faixa_etaria(idade: int, faixas) -> str:
    """Nome da faixa etária de uma idade. `faixas` é uma lista de (mínimo, máximo)."""
    for minimo, maximo in faixas:
        if minimo <= idade <= maximo:
            return rotulo_faixa(minimo, maximo)
    return FORA_DAS_FAIXAS


def subtrair_anos(data: date, anos: int) -> date:
    """Mesma data, `anos` atrás (29/02 vira 28/02 quando o ano não é bissexto)."""
    try:
        return data.replace(year=data.year - anos)
    except ValueError:
        return data.replace(year=data.year - anos, day=28)


def intervalo_nascimento(idade_minima: int, idade_maxima: int, hoje: date) -> tuple[date, date]:
    """Datas de nascimento de quem tem entre `idade_minima` e `idade_maxima` anos hoje.

    Devolve (nascido_depois_de, nascido_ate): a primeira data é exclusiva e a
    segunda é inclusiva.
    """
    nascido_depois_de = subtrair_anos(hoje, idade_maxima + 1)
    nascido_ate = subtrair_anos(hoje, idade_minima)
    return nascido_depois_de, nascido_ate


# --- Protocolo -------------------------------------------------------------


def gerar_protocolo(ano: int, numero: int, prefixo: str = "SEM") -> str:
    """Ex.: gerar_protocolo(2026, 123) -> 'SEM-2026-000123'."""
    return f"{prefixo}-{ano}-{numero:06d}"
