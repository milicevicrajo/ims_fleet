import sys

from django.core.exceptions import ImproperlyConfigured

from .base import *


# `manage.py` podrazumeva bas ovaj modul podesavanja. Otkako 'default' pokazuje na
# stvarnu bazu, `python manage.py test` bi pokusao da nad njom napravi test bazu
# (CREATE DATABASE test_<ime>) i da je na kraju obrise. Testovi imaju svoja
# podesavanja (SQLite u memoriji), pa se ovde odbijaju umesto da se izvrse.
if 'test' in sys.argv:
    raise ImproperlyConfigured(
        'Testovi se ne pokrecu nad podesavanjima za razvoj jer ona koriste stvarnu '
        'bazu. Koristi: python manage.py test --settings=ims_erp.settings.testing'
    )


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
# Pristupni podaci se citaju iz .env (vidi .env.example) — nisu u repozitorijumu.
ALLOWED_HOSTS = ['127.0.0.1']

DATABASES = {
    # Za rad nad stvarnom bazom umesto SQLite-a, zameni 'default' sa:
    'default': {'ENGINE': 'mssql', **database_credentials()},
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # },

    'server_db': {
        'ENGINE': 'mssql',
        **database_credentials(),
    },
}

DATABASES = apply_mssql_connection_defaults(DATABASES)
