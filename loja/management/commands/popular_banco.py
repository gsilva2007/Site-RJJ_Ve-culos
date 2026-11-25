# Comando customizado para criar registros de demonstracao.

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from pathlib import Path
from django.conf import settings
from django.core.files import File
from loja.models import FotoVeiculo
from loja.models import Marca, Cliente, Veiculo
from loja.services import registrar_movimentacao

class Command(BaseCommand):
    help = 'Insere alguns registros fictícios para demonstrar o projeto (sem alterar os existentes).'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        marcas = {}
        for nome in ['Fiat', 'Honda', 'Volkswagen', 'Chevrolet', 'Ford']:
            marcas[nome], _ = Marca.objects.get_or_create(nome=nome)
        for nome, telefone in [('João Silva', '(18) 99999-1111'), ('Maria Santos', '(18) 99999-2222'), ('Pedro Oliveira', '(18) 99999-3333')]:
            Cliente.objects.get_or_create(nome=nome, defaults={'telefone': telefone})
        registros = [('Fiat', 'Siena', 2010, '28900', 171000, 'Manual', 'Flex', '1.0'), ('Honda', 'Civic LXL', 2011, '54990', 140000, 'Automático', 'Flex', '1.8'), ('Volkswagen', 'Gol', 2014, '34900', 98000, 'Manual', 'Flex', '1.0'), ('Chevrolet', 'Onix', 2016, '49900', 82000, 'Manual', 'Flex', '1.4'), ('Ford', 'Ka', 2018, '42900', 75000, 'Manual', 'Flex', '1.0')]
        for i, (marca, modelo, ano, preco, km, cambio, comb, motor) in enumerate(registros):
            v, novo = Veiculo.objects.get_or_create(marca=marcas[marca], modelo=modelo, ano=ano, defaults={'preco': Decimal(preco), 'quilometragem': km, 'cambio': cambio, 'combustivel': comb, 'motor': motor, 'destaque': i < 3})
            if novo:
                registrar_movimentacao(v, 'entrada', None, 'Exemplo criado pelo popular_banco')
            demo = {'Siena': 'siena.jpg', 'Civic LXL': 'civic.jpg'}.get(modelo)
            if demo and (not v.fotos.exists()):
                arq = Path(settings.BASE_DIR) / 'static' / 'img' / 'demo' / demo
                with arq.open('rb') as fp:
                    foto = FotoVeiculo(veiculo=v)
                    foto.imagem.save(demo, File(fp), save=True)
        self.stdout.write(self.style.SUCCESS('Dados fictícios preparados. Adicione fotos reais pelo painel.'))
