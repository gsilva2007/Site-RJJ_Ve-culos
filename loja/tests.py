# Testes automatizados dos fluxos principais da loja.

from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Marca, Veiculo, ItemInteresse, Movimentacao, Movimento

class FluxosPrincipaisTests(TestCase):

    def setUp(self):
        self.marca = Marca.objects.create(nome='Fiat')
        self.carro = Veiculo.objects.create(marca=self.marca, modelo='Siena', ano=2010, preco=Decimal('28900'), quilometragem=171000)
        self.cliente = User.objects.create_user('cliente', password='SenhaForte123!')
        self.admin = User.objects.create_user('gestor', password='SenhaForte123!', is_staff=True)

    def test_catalogo_publico(self):
        response = self.client.get(reverse('catalogo'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Siena')

    def test_cliente_nao_acessa_painel(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('painel')).status_code, 403)

    def test_admin_acessa_painel(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('painel'), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_interesse_exige_login(self):
        response = self.client.post(reverse('alternar_interesse', args=[self.carro.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ItemInteresse.objects.count(), 0)

    def test_interesse_salvar_e_remover(self):
        self.client.force_login(self.cliente)
        url = reverse('alternar_interesse', args=[self.carro.pk])
        self.client.post(url)
        self.assertEqual(ItemInteresse.objects.count(), 1)
        self.client.post(url)
        self.assertEqual(ItemInteresse.objects.count(), 0)

    def test_novo_veiculo_gera_movimentacao(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('novo_admin', args=['veiculos']), {'marca': self.marca.pk, 'modelo': 'Palio', 'ano': 2015, 'preco': '30000', 'quilometragem': '80000', 'cambio': 'Manual', 'combustivel': 'Flex', 'motor': '1.0', 'cor': 'Prata', 'descricao': 'Veículo de teste', 'status': 'disponivel'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Movimentacao.objects.filter(veiculo__modelo='Palio').exists())

    def test_consultas_administrativas(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('consultas')).status_code, 200)

    def test_detalhes_admin_protegido(self):
        url = reverse('detalhe_admin', args=['veiculos', self.carro.pk])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_movimentacao_manual_altera_estoque(self):
        self.client.force_login(self.admin)
        saida = Movimento.objects.create(nome='Saída manual', tipo='saida')
        response = self.client.post(reverse('movimentacoes'), {
            'movimento': saida.pk, 'veiculo': self.carro.pk, 'observacao': 'Saída de teste',
        })
        self.assertEqual(response.status_code, 302)
        self.carro.refresh_from_db()
        self.assertEqual(self.carro.status, 'vendido')
        self.assertEqual(Movimentacao.objects.filter(veiculo=self.carro).count(), 1)

    def test_movimentacao_repetida_impedida(self):
        self.client.force_login(self.admin)
        saida = Movimento.objects.create(nome='Saída manual', tipo='saida')
        self.carro.status = 'vendido'
        self.carro.save()
        response = self.client.post(reverse('movimentacoes'), {
            'movimento': saida.pk, 'veiculo': self.carro.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Movimentacao.objects.count(), 0)

    def test_cadastro_preserva_destino(self):
        url = reverse('cadastro') + '?next=' + reverse('detalhe', args=[self.carro.pk])
        response = self.client.post(url, {
            'username': 'novo_cliente', 'email': 'novo@example.com',
            'password1': 'SenhaForte123!', 'password2': 'SenhaForte123!',
            'next': reverse('detalhe', args=[self.carro.pk]),
        })
        self.assertRedirects(response, reverse('detalhe', args=[self.carro.pk]))

    def test_exclusao_veiculo_com_historico_bloqueada(self):
        self.client.force_login(self.admin)
        movimento = Movimento.objects.create(nome='Entrada de teste', tipo='entrada')
        Movimentacao.objects.create(veiculo=self.carro, movimento=movimento)
        self.client.post(reverse('excluir_admin', args=['veiculos', self.carro.pk]))
        self.assertTrue(Veiculo.objects.filter(pk=self.carro.pk).exists())
