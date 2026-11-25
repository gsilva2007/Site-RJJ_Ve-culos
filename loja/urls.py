
# Rotas: associam os caminhos do navegador às funções em views.py.

from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views


urlpatterns = [
    # Páginas públicas
    path('', views.inicio, name='inicio'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('veiculo/<int:pk>/', views.detalhe, name='detalhe'),
    path('sobre/', views.sobre, name='sobre'),

    # Autenticação
    path('entrar/', views.entrar, name='entrar'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('sair/', LogoutView.as_view(), name='sair'),

    # Veículos salvos
    path('meus-veiculos/', views.meus_veiculos, name='meus_veiculos'),
    path(
        'interesse/<int:pk>/',
        views.alternar_interesse,
        name='alternar_interesse'
    ),

    # Painel administrativo
    path('painel/', views.painel, name='painel'),
    path(
        'painel/movimentacoes/',
        views.movimentacoes,
        name='movimentacoes'
    ),
    path(
        'painel/consultas/',
        views.consultas,
        name='consultas'
    ),

    # Fotografias
    path(
        'painel/foto/<int:pk>/excluir/',
        views.excluir_foto,
        name='excluir_foto'
    ),

    # Criação automática por URL
    path(
        'painel/<str:tipo>/criar/',
        views.criar_automatico,
        name='criar_automatico'
    ),

    # CRUD administrativo
    path(
        'painel/<str:tipo>/',
        views.lista_admin,
        name='lista_admin'
    ),
    path(
        'painel/<str:tipo>/novo/',
        views.editar_admin,
        name='novo_admin'
    ),
    path(
        'painel/<str:tipo>/<int:pk>/detalhes/',
        views.detalhe_admin,
        name='detalhe_admin'
    ),
    path(
        'painel/<str:tipo>/<int:pk>/editar/',
        views.editar_admin,
        name='editar_admin'
    ),
    path(
        'painel/<str:tipo>/<int:pk>/excluir/',
        views.excluir_admin,
        name='excluir_admin'
    ),
]
