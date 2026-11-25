# Formularios: validam dados enviados por visitantes e administradores.

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Marca, Cliente, Veiculo, Movimento, Movimentacao, FotoVeiculo

User = get_user_model()

class CadastroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('E-mail já cadastrado.')
        return email

class MarcaForm(forms.ModelForm):

    class Meta:
        model = Marca
        fields = ['nome']


class ClienteForm(forms.ModelForm):
    conta_ativa = forms.BooleanField(
        required=False,
        label='Conta ativa',
        help_text='Desmarque para bloquear o acesso do cliente.'
    )

    nova_senha = forms.CharField(
        required=False,
        label='Nova senha',
        widget=forms.PasswordInput,
        help_text='Deixe vazio para manter a senha atual.'
    )

    confirmar_senha = forms.CharField(
        required=False,
        label='Confirmar nova senha',
        widget=forms.PasswordInput
    )

    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        usuario = (
            self.instance.usuario
            if self.instance.pk and self.instance.usuario_id
            else None
        )

        if usuario and not usuario.is_staff:
            self.fields['conta_ativa'].initial = usuario.is_active
        else:
            self.fields.pop('conta_ativa')
            self.fields.pop('nova_senha')
            self.fields.pop('confirmar_senha')

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '')

        if telefone:
            numeros = ''.join(c for c in telefone if c.isdigit())

            if len(numeros) < 10:
                raise forms.ValidationError(
                    'Informe um telefone válido com DDD.'
                )

        return telefone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()

        if self.instance.pk and self.instance.usuario_id and email:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            existe = User.objects.filter(
                email__iexact=email
            ).exclude(
                pk=self.instance.usuario_id
            ).exists()

            if existe:
                raise forms.ValidationError(
                    'Este e-mail já pertence a outra conta.'
                )

        return email

    def clean(self):
        dados = super().clean()

        senha = dados.get('nova_senha', '')
        confirmacao = dados.get('confirmar_senha', '')

        if senha or confirmacao:
            if senha != confirmacao:
                raise forms.ValidationError(
                    'As senhas informadas não coincidem.'
                )

            from django.contrib.auth.password_validation import validate_password

            usuario = self.instance.usuario if self.instance.pk else None

            if not usuario or usuario.is_staff:
                raise forms.ValidationError(
                    'Esta conta não pode ter a senha alterada aqui.'
                )

            validate_password(senha, user=usuario)

        return dados

    def save(self, commit=True):
        cliente = super().save(commit=commit)

        if commit and cliente.usuario_id:
            usuario = cliente.usuario

            if not usuario.is_staff:
                usuario.email = cliente.email
                usuario.is_active = self.cleaned_data['conta_ativa']

                campos = ['email', 'is_active']

                senha = self.cleaned_data.get('nova_senha')

                if senha:
                    usuario.set_password(senha)
                    campos.append('password')

                usuario.save(update_fields=campos)

        return cliente


class VeiculoForm(forms.ModelForm):

    # Validação exibida no formulário e repetida pelo servidor.
    def clean_preco(self):
        valor = self.cleaned_data['preco']
        if valor <= 0:
            raise forms.ValidationError('O preço precisa ser positivo.')
        return valor

    class Meta:
        model = Veiculo
        fields = ['marca', 'modelo', 'ano', 'preco', 'quilometragem', 'cambio', 'combustivel', 'motor', 'cor', 'descricao', 'status', 'destaque']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 3})}

class FotoForm(forms.ModelForm):

    class Meta:
        model = FotoVeiculo
        fields = ['imagem', 'legenda']

class MovimentoForm(forms.ModelForm):

    class Meta:
        model = Movimento
        fields = ['nome', 'tipo']

class MovimentacaoForm(forms.ModelForm):
    def clean(self):
        dados = super().clean()
        veiculo = dados.get('veiculo')
        movimento = dados.get('movimento')
        if veiculo and movimento:
            if movimento.tipo == 'entrada' and veiculo.status == 'disponivel':
                raise forms.ValidationError('O veículo já consta como disponível no estoque.')
            if movimento.tipo == 'saida' and veiculo.status == 'vendido':
                raise forms.ValidationError('O veículo já consta como vendido.')
        return dados

    class Meta:
        model = Movimentacao
        fields = ['movimento', 'veiculo', 'observacao']
