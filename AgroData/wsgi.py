"""
WSGI config for AgroData project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# CORREÇÃO: ADICIONA O CAMINHO DO VIRTUAL ENVIRONMENT (VENV) AO PYTHON PATH
# O mod_wsgi está falhando ao reconhecer o python-home do Apache.
# Forçar o caminho aqui garante que o módulo 'django' e 'AgroData' sejam encontrados.
sys.path.insert(0, '/var/www/univesp/venv/lib/python3.10/site-packages')
sys.path.insert(0, '/var/www/univesp')

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgroData.settings')

application = get_wsgi_application()