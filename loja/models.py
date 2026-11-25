# Modelos: cada classe representa uma tabela ou relacionamento do banco de dados.

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date

class Marca(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Cliente(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_cliente'
    )
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Veiculo(models.Model):
    CAMBIO = [('Manual', 'Manual'), ('Automático', 'Automático'), ('CVT', 'CVT')]
    COMBUSTIVEL = [('Flex', 'Flex'), ('Gasolina', 'Gasolina'), ('Diesel', 'Diesel'), ('Elétrico', 'Elétrico'), ('Híbrido', 'Híbrido')]
    STATUS = [('disponivel', 'Disponível'), ('reservado', 'Reservado'), ('vendido', 'Vendido')]
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name='veiculos')
    modelo = models.CharField(max_length=100)
    ano = models.PositiveSmallIntegerField(validators=[MinValueValidator(1950)])
    preco = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    quilometragem = models.PositiveIntegerField(default=0)
    cambio = models.CharField(max_length=16, choices=CAMBIO, default='Manual')
    combustivel = models.CharField(max_length=16, choices=COMBUSTIVEL, default='Flex')
    motor = models.CharField(max_length=30, blank=True)
    cor = models.CharField(max_length=40, blank=True)
    descricao = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default='disponivel')
    destaque = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.marca} {self.modelo} {self.ano}'

    def clean(self):
        if self.ano and self.ano > date.today().year + 1:
            raise ValidationError({'ano': 'O ano não pode superar o próximo ano.'})

    @property
    def foto_principal(self):
        return self.fotos.first()

class FotoVeiculo(models.Model):
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='veiculos/%Y/%m/')
    legenda = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'Foto de {self.veiculo}'

class ItemInteresse(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interesses')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='interessados')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['usuario', 'veiculo'], name='item_interesse_unico')]
        ordering = ['-criado_em']

class Movimento(models.Model):
    nome = models.CharField(max_length=60, unique=True)
    tipo = models.CharField(max_length=7, choices=[('entrada', 'Entrada'), ('saida', 'Saída')])

    def __str__(self):
        return self.nome

class Movimentacao(models.Model):
    movimento = models.ForeignKey(Movimento, on_delete=models.PROTECT)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name='movimentacoes')
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True)
    observacao = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'{self.movimento} - {self.veiculo}'
