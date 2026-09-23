from django.contrib import admin
from .models import Equipe, Prioridade, SLA, Categoria, Chamado

@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ("nome", "email_contato", "ativa")

@admin.register(Prioridade)
class PrioridadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "nivel", "peso", "cor_badge")

@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ("prioridade", "horas_resolucao", "descricao")

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "equipe", "ativa")
    list_filter = ("equipe", "ativa")

@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ("protocolo", "titulo", "solicitante_nome", "categoria", "prioridade", "status", "prazo_sla", "dentro_do_prazo")
    list_filter = ("status", "prioridade", "categoria")
    search_fields = ("protocolo", "titulo", "solicitante_nome")
