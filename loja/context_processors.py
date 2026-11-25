# Dados compartilhados pelos templates (contador de itens salvos).

from .models import ItemInteresse

def carrinho(request):
    return {'quantidade_interesses': ItemInteresse.objects.filter(usuario=request.user).count() if request.user.is_authenticated else 0}
