"""Variáveis disponíveis em todos os templates."""
from django.conf import settings

from apps.contas.perfis import eh_administrador, eh_equipe
from apps.matriculas.models import Matricula


def area_interna(request):
    """Informa o perfil do usuário e o total de matrículas pendentes."""
    usuario = getattr(request, "user", None)
    equipe = eh_equipe(usuario)
    contexto = {
        "nome_ong": settings.NOME_ONG,
        "eh_equipe": equipe,
        "eh_administrador": eh_administrador(usuario),
    }
    if equipe:
        contexto["total_pendentes"] = Matricula.objects.filter(
            status=Matricula.Status.PENDENTE
        ).count()
    return contexto
