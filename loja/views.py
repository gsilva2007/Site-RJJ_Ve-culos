# Views: recebem requisicoes HTTP, consultam modelos e renderizam os templates.

from django.views.decorators.http import require_http_methods
from datetime import datetime
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Sum, Q, Case, When, IntegerField
from django.db.models.functions import ExtractMonth
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import CadastroForm, MarcaForm, ClienteForm, VeiculoForm, FotoForm, MovimentoForm, MovimentacaoForm
from .models import Marca, Cliente, Veiculo, FotoVeiculo, ItemInteresse, Movimento, Movimentacao
from .services import registrar_movimentacao, registrar_movimentacao_manual
WHATSAPP = '5518996673577'

def inicio(request):
    carros = Veiculo.objects.filter(status='disponivel').select_related('marca').prefetch_related('fotos')
    destaques = carros.filter(destaque=True)[:3]
    if not destaques:
        destaques = carros[:3]
    return render(request, 'loja/inicio.html', {'veiculos': destaques})

def catalogo(request):
    qs = Veiculo.objects.filter(status='disponivel').select_related('marca').prefetch_related('fotos')
    busca = request.GET.get('busca', '').strip()
    marca = request.GET.get('marca', '').strip()
    ano = request.GET.get('ano', '').strip()
    if busca:
        qs = qs.filter(Q(modelo__icontains=busca) | Q(marca__nome__icontains=busca) | Q(descricao__icontains=busca))
    if marca.isdigit():
        qs = qs.filter(marca_id=int(marca))
    if ano.isdigit():
        qs = qs.filter(ano=int(ano))
    return render(request, 'loja/catalogo.html', {'veiculos': qs, 'marcas': Marca.objects.all(), 'anos': Veiculo.objects.values_list('ano', flat=True).distinct().order_by('-ano'), 'busca': busca, 'marca_atual': marca, 'ano_atual': ano})

def detalhe(request, pk):
    veiculo = get_object_or_404(Veiculo.objects.select_related('marca').prefetch_related('fotos'), pk=pk)
    if veiculo.status != 'disponivel' and (not (request.user.is_authenticated and request.user.is_staff)):
        raise Http404('Veículo indisponível')
    salvo = request.user.is_authenticated and ItemInteresse.objects.filter(usuario=request.user, veiculo=veiculo).exists()
    return render(request, 'loja/detalhe.html', {'veiculo': veiculo, 'fotos': veiculo.fotos.all(), 'salvo': salvo, 'whatsapp': WHATSAPP})

def sobre(request):
    return render(request, 'loja/sobre.html', {'whatsapp': WHATSAPP})

def entrar(request):
    if request.user.is_authenticated:
        return redirect('painel' if request.user.is_staff else 'inicio')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        destino = request.POST.get('next') or request.GET.get('next', '')
        if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(destino)
        return redirect('painel' if request.user.is_staff else 'inicio')
    return render(request, 'loja/login.html', {'form': form, 'proximo': request.GET.get('next', '')})

def cadastro(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    form = CadastroForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            

            Cliente.objects.create(
                usuario=user,
                nome=user.username,
                email=user.email,
                telefone=''
            )

        login(request, user)
        messages.success(request, 'Conta criada com sucesso!')

        destino = (
            request.POST.get('next')
            or request.GET.get('next', '')
        )

        if destino and url_has_allowed_host_and_scheme(
            destino,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()
        ):
            return redirect(destino)

        return redirect('inicio')

    return render(
        request,
        'loja/cadastro.html',
        {
            'form': form,
            'proximo': request.GET.get('next', '')
        }
    )

@login_required
@require_POST
def alternar_interesse(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk, status='disponivel')
    item, criado = ItemInteresse.objects.get_or_create(usuario=request.user, veiculo=veiculo)
    if not criado:
        item.delete()
        messages.info(request, 'Veículo removido dos salvos.')
    else:
        messages.success(request, 'Veículo adicionado aos seus salvos.')
    return redirect(request.POST.get('voltar') if request.POST.get('voltar', '').startswith('/') and (not request.POST.get('voltar', '').startswith('//')) else 'meus_veiculos')

@login_required
def meus_veiculos(request):
    itens = ItemInteresse.objects.filter(usuario=request.user, veiculo__status='disponivel').select_related('veiculo', 'veiculo__marca').prefetch_related('veiculo__fotos')
    return render(request, 'loja/meus_veiculos.html', {'itens': itens, 'whatsapp': WHATSAPP})

def admin_required(view):

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied('Somente administradores.')
        return view(request, *args, **kwargs)
    return wrapper
TIPOS = {'marcas': (Marca, MarcaForm, 'Marcas'), 'clientes': (Cliente, ClienteForm, 'Clientes'), 'veiculos': (Veiculo, VeiculoForm, 'Veículos'), 'movimentos': (Movimento, MovimentoForm, 'Tipos de movimento')}

@admin_required
def painel(request):
    return redirect('lista_admin', tipo='veiculos')

@admin_required
def lista_admin(request, tipo):
    if tipo not in TIPOS:
        raise Http404()

    model, form, titulo = TIPOS[tipo]

    qs = model.objects.all()

    # Relaciona os clientes com seus usuários
    if tipo == 'clientes':
        qs = qs.select_related('usuario')

    # Pesquisa dos registros
    busca = request.GET.get('busca', '').strip()

    if busca:
        if tipo == 'clientes':
            qs = qs.filter(
                Q(nome__icontains=busca)
                | Q(email__icontains=busca)
                | Q(usuario__username__icontains=busca)
            )
        else:
            field = {
                'marcas': 'nome',
                'veiculos': 'modelo',
                'movimentos': 'nome'
            }[tipo]

            qs = qs.filter(
                **{field + '__icontains': busca}
            )

    if tipo == 'veiculos':
        qs = qs.select_related('marca').prefetch_related('fotos')

        status = request.GET.get('status', '')

        if status in ['disponivel', 'reservado', 'vendido']:
            qs = qs.filter(status=status)

    return render(
        request,
        'loja/admin/lista.html',
        {
            'tipo': tipo,
            'titulo': titulo,
            'objetos': qs,
            'busca': busca,
            'status_atual': request.GET.get('status', '')
        }
    )

@admin_required
def detalhe_admin(request, tipo, pk):
    """READ: visualização individual de um registro, além da listagem do CRUD."""
    if tipo not in TIPOS:
        raise Http404()
    model, _, titulo = TIPOS[tipo]
    obj = get_object_or_404(model, pk=pk)
    return render(request, 'loja/admin/detalhes.html', {
        'obj': obj, 'tipo': tipo, 'titulo': titulo,
    })


@admin_required
def editar_admin(request, tipo, pk=None):
    if tipo not in TIPOS:
        raise Http404()
    model, form_class, titulo = TIPOS[tipo]
    obj = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            anterior = Veiculo.objects.get(pk=obj.pk).status if tipo == 'veiculos' and obj else None
            salvo = form.save()
            if tipo == 'clientes' and salvo.usuario_id:
                usuario = salvo.usuario
                if usuario.email != salvo.email:
                    usuario.email = salvo.email
                    usuario.save(update_fields=['email'])
            if tipo == 'veiculos':
                fotos = request.FILES.getlist('fotos')
                if len(fotos) > 8 or len(fotos) + salvo.fotos.count() > 12:
                    form.add_error(None, 'Limite de 8 fotos por envio e 12 por veículo.')
                    transaction.set_rollback(True)
                else:
                    for foto in fotos:
                        if not foto.content_type.startswith('image/') or foto.size > 5 * 1024 * 1024:
                            form.add_error(None, 'As fotos devem ser imagens de até 5 MB.')
                            transaction.set_rollback(True)
                            break
                        FotoVeiculo.objects.create(veiculo=salvo, imagem=foto)
                    if not form.errors and (not obj or anterior != salvo.status):
                        registrar_movimentacao(salvo, 'entrada' if salvo.status == 'disponivel' else 'saida', request.user, 'Cadastro' if not obj else f'Status: {anterior} → {salvo.status}')
        if not form.errors:
            messages.success(request, 'Registro salvo com sucesso.')
            return redirect('lista_admin', tipo=tipo)
    return render(request, 'loja/admin/form.html', {'form': form, 'obj': obj, 'tipo': tipo, 'titulo': titulo})


@admin_required
@require_http_methods(["GET", "POST"])
def criar_automatico(request, tipo):
    if tipo not in ('marcas', 'clientes', 'veiculos'):
        raise Http404()

    if request.method == 'POST':
        with transaction.atomic():

            if tipo == 'marcas':
                numero = 1

                while Marca.objects.filter(
                    nome=f'Marca {numero}'
                ).exists():
                    numero += 1

                registro = Marca.objects.create(
                    nome=f'Marca {numero}'
                )

            elif tipo == 'clientes':
                numero = 1

                while Cliente.objects.filter(
                    nome=f'Cliente Teste {numero}'
                ).exists():
                    numero += 1

                registro = Cliente.objects.create(
                    nome=f'Cliente Teste {numero}',
                    telefone='(18) 99999-9999',
                    email=f'cliente.teste.{numero}@example.com'
                )

            else:
                marca = Marca.objects.first()

                if marca is None:
                    messages.error(
                        request,
                        'Cadastre uma marca antes de criar um veículo.'
                    )
                    return redirect(
                        'lista_admin',
                        tipo='veiculos'
                    )

                numero = 1

                while Veiculo.objects.filter(
                    modelo=f'Veículo Teste {numero}'
                ).exists():
                    numero += 1

                registro = Veiculo.objects.create(
                    marca=marca,
                    modelo=f'Veículo Teste {numero}',
                    ano=2020,
                    preco=50000,
                    quilometragem=30000,
                    cambio='Manual',
                    combustivel='Flex',
                    descricao='Cadastro automático para teste de rotas.',
                    status='disponivel'
                )

        messages.success(
            request,
            f'Registro criado com sucesso! ID: {registro.pk}'
        )

        return redirect('lista_admin', tipo=tipo)

    return render(
        request,
        'loja/admin/confirmar_operacao.html',
        {
            'tipo': tipo,
            'acao': 'criar',
            'titulo': 'Criação automática',
        }
    )


@admin_required
@require_http_methods(["GET", "POST"])
def excluir_admin(request, tipo, pk):
    if tipo not in TIPOS:
        raise Http404()

    model, _, titulo = TIPOS[tipo]

    obj = get_object_or_404(model, pk=pk)

    if request.method == 'POST':
        from django.db.models.deletion import ProtectedError

        try:
            obj.delete()

            messages.success(
                request,
                'Registro excluído com sucesso.'
            )

        except ProtectedError:
            messages.error(
                request,
                'Não é possível excluir este registro '
                'porque existem dados vinculados.'
            )

        return redirect('lista_admin', tipo=tipo)

    return render(
        request,
        'loja/admin/confirmar_operacao.html',
        {
            'tipo': tipo,
            'titulo': titulo,
            'acao': 'excluir',
            'obj': obj
        }
    )

@admin_required
@require_POST
def excluir_foto(request, pk):
    foto = get_object_or_404(FotoVeiculo, pk=pk)
    veiculo_id = foto.veiculo_id
    foto.delete()
    messages.success(request, 'Foto removida.')
    return redirect('editar_admin', tipo='veiculos', pk=veiculo_id)

@admin_required
def movimentacoes(request):
    qs = Movimentacao.objects.select_related('movimento', 'veiculo', 'responsavel')
    data = request.GET.get('tipo', '')
    if data in ('entrada', 'saida'):
        qs = qs.filter(movimento__tipo=data)
    form = MovimentacaoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            registrar_movimentacao_manual(form, request.user)
        except ValueError as erro:
            form.add_error(None, str(erro))
        else:
            messages.success(request, 'Movimentação registrada e estoque atualizado.')
            return redirect('movimentacoes')
    return render(request, 'loja/admin/movimentacoes.html', {'movimentacoes': qs[:200], 'form': form, 'tipo_atual': data})

@admin_required
def consultas(request):
    totais = Marca.objects.annotate(total_veiculos=Count('veiculos', distinct=True), total_movimentacoes=Count('veiculos__movimentacoes', distinct=True)).order_by('nome')
    agrupamento = Veiculo.objects.values('marca__nome', 'status').annotate(quantidade=Count('id'), valor_total=Sum('preco')).order_by('marca__nome', 'status')
    pivot = Marca.objects.annotate(entradas=Count('veiculos__movimentacoes', filter=Q(veiculos__movimentacoes__movimento__tipo='entrada')), saidas=Count('veiculos__movimentacoes', filter=Q(veiculos__movimentacoes__movimento__tipo='saida'))).order_by('nome')
    return render(request, 'loja/admin/consultas.html', {'totais': totais, 'agrupamento': agrupamento, 'pivot': pivot})
