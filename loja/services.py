# Regras de negócio do estoque: movimentos ficam registrados para auditoria.
from django.db import transaction
from .models import Movimento, Movimentacao


def registrar_movimentacao(veiculo, tipo, usuario, observacao=''):
    """Cria uma movimentação; deve ser usado numa transação no cadastro de veículo."""
    if tipo not in ('entrada', 'saida'):
        raise ValueError('Tipo de movimento desconhecido.')
    nome = 'Entrada no estoque' if tipo == 'entrada' else 'Saída do estoque'
    movimento, _ = Movimento.objects.get_or_create(nome=nome, defaults={'tipo': tipo})
    return Movimentacao.objects.create(
        veiculo=veiculo, movimento=movimento,
        responsavel=usuario, observacao=observacao,
    )


@transaction.atomic
def registrar_movimentacao_manual(form, usuario):
    """Registra entrada ou saída e atualiza o status na mesma transação."""
    movimento = form.cleaned_data['movimento']
    veiculo = form.cleaned_data['veiculo']
    # Bloqueia o objeto enquanto a transação é processada (onde suportado).
    veiculo = type(veiculo).objects.select_for_update().get(pk=veiculo.pk)
    if movimento.tipo == 'entrada' and veiculo.status == 'disponivel':
        raise ValueError('O veículo já está disponível.')
    if movimento.tipo == 'saida' and veiculo.status == 'vendido':
        raise ValueError('O veículo já está vendido.')
    registro = form.save(commit=False)
    registro.responsavel = usuario
    registro.save()
    veiculo.status = 'disponivel' if movimento.tipo == 'entrada' else 'vendido'
    veiculo.save(update_fields=['status'])
    return registro
