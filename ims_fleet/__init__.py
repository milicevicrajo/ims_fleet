from __future__ import absolute_import, unicode_literals					
					
# Obezbedi da je Celery aplikacija uvek dostupna					
from .celery import app as celery_app					
					
__all__ = ['celery_app']					
