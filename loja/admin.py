# Configuracao do painel nativo do Django, distinto do painel RJJ.

from django.contrib import admin
from .models import Marca, Cliente, Veiculo, FotoVeiculo, ItemInteresse, Movimento, Movimentacao

class FotoInline(admin.TabularInline):
    model = FotoVeiculo
    extra = 1

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'marca', 'ano', 'preco', 'status', 'destaque')
    list_filter = ('marca', 'status', 'ano')
    search_fields = ('modelo', 'marca__nome')
    inlines = [FotoInline]
admin.site.register([Marca, Cliente, ItemInteresse, Movimento, Movimentacao])
