# Entrada ASGI alternativa, nao usada diretamente pelo Apache.

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.core.asgi import get_asgi_application
application = get_asgi_application()
