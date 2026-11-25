from django.contrib import admin

from .models import Atividade, Matricula


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "idade_minima", "idade_maxima", "vagas", "ativa")
    list_filter = ("ativa",)
    search_fields = ("nome",)


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ("protocolo", "crianca", "atividade", "status", "data_solicitacao", "origem")
    list_filter = ("status", "atividade", "origem")
    search_fields = ("protocolo", "crianca__nome")
    autocomplete_fields = ("crianca", "atividade")
    readonly_fields = (
        "protocolo",
        "data_aprovacao",
        "aprovada_por",
        "alterada_por",
        "data_consentimento",
        "versao_termo",
    )
