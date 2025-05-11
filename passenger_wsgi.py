import os
import sys

# 1) Add your project root (where manage.py lives) to PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

# 2) Tell Django which settings module to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_site.settings')

# 3) Get the WSGI application and expose it as 'application'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
