# Entrada WSGI usada na implantacao com Apache/mod_wsgi.

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
