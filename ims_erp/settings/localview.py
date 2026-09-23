"""Samo za vizuelnu proveru: fajl SQLite, bez SQL Servera."""
from ims_erp.settings.testing import *  # noqa

DEBUG = True
_NAME = r'C:\Users\rajom\AppData\Local\Temp\claude\c--Users-rajom-Desktop-Posao-02-IMS-FLOTA-ims-fleet\c8b12be7-87ab-406b-81f6-e5bfd96216aa\scratchpad\localview.sqlite3'
DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': _NAME},
    'server_db': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': _NAME},
}
