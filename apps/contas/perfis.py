"""Perfis de acesso da equipe.

- Administrador: acesso total (excluir, exportar, gerenciar usuários).
- Atendente: cadastra, consulta, edita e aprova matrículas.

Cada perfil é um grupo do Django com o mesmo nome.
"""
from django.contrib.auth.models import Group
from django.db.utils import OperationalError, ProgrammingError

ADMINISTRADOR = "Administrador"
ATENDENTE = "Atendente"
PERFIS = (ADMINISTRADOR, ATENDENTE)


def criar_perfis_padrao():
    """Cria os dois grupos, se ainda não existirem."""
    for nome in PERFIS:
        Group.objects.get_or_create(name=nome)


def criar_perfis_apos_migrate(sender, **kwargs):
    """Chamado pelo sinal post_migrate (veja apps.py)."""
    if getattr(sender, "label", "") != "auth":
        return
    try:
        criar_perfis_padrao()
    except (OperationalError, ProgrammingError):
        # A tabela de grupos ainda não existe (migrate parcial).
        pass


def perfis_do_usuario(usuario) -> set[str]:
    """Nomes dos grupos do usuário (guardados para não repetir a consulta)."""
    if not hasattr(usuario, "_perfis_cache"):
        usuario._perfis_cache = set(usuario.groups.values_list("name", flat=True))
    return usuario._perfis_cache


def _ativo(usuario) -> bool:
    return bool(usuario and usuario.is_authenticated and usuario.is_active)


def eh_administrador(usuario) -> bool:
    if not _ativo(usuario):
        return False
    return usuario.is_superuser or ADMINISTRADOR in perfis_do_usuario(usuario)


def eh_equipe(usuario) -> bool:
    """True para quem pode entrar na área interna (qualquer um dos perfis)."""
    if not _ativo(usuario):
        return False
    return usuario.is_superuser or bool(perfis_do_usuario(usuario) & set(PERFIS))


def perfil_atual(usuario) -> str:
    """Perfil exibido nas telas: Administrador tem prioridade."""
    perfis = perfis_do_usuario(usuario)
    if usuario.is_superuser or ADMINISTRADOR in perfis:
        return ADMINISTRADOR
    if ATENDENTE in perfis:
        return ATENDENTE
    return ""


def definir_perfil(usuario, nome: str):
    """Deixa o usuário com exatamente um perfil."""
    if nome not in PERFIS:
        raise ValueError(f"Perfil desconhecido: {nome}")
    criar_perfis_padrao()
    usuario.groups.remove(*Group.objects.filter(name__in=PERFIS))
    usuario.groups.add(Group.objects.get(name=nome))
    if hasattr(usuario, "_perfis_cache"):
        del usuario._perfis_cache
