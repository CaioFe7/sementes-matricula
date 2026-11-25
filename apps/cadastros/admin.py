from django.contrib import admin

from .models import Bairro, Crianca, Responsavel


@admin.register(Bairro)
class BairroAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "bairro")
    list_filter = ("bairro", "parentesco")
    search_fields = ("nome", "cpf")
    autocomplete_fields = ("bairro",)


@admin.register(Crianca)
class CriancaAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_nascimento", "sexo", "bairro", "responsavel")
    list_filter = ("sexo", "bairro")
    search_fields = ("nome", "responsavel__nome", "responsavel__cpf")
    autocomplete_fields = ("bairro", "responsavel", "outros_responsaveis")
