from __future__ import absolute_import, unicode_literals					
import os					
from celery import Celery		
import sys			

# Rešenje za 'isatty' grešku
sys.stdin = None	

# Postavi default Django postavke za Celery					
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_fleet.settings.production')					
					
app = Celery('ims_fleet')					
print("Celery broker URL:", app.conf.broker_url)


# Konfiguracija Celery iz Django postavki, koristi namespace "CELERY_"					
app.config_from_object('django.conf:settings', namespace='CELERY')					
		
# Automatsko otkrivanje task-ova iz aplikacija					
app.autodiscover_tasks()					
print("Registrovani zadaci:", app.tasks.keys())			
@app.task(bind=True)					
def debug_task(self):					
    print(f'Request: {self.request!r}')					
