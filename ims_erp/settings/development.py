from .base import *


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
# Pristupni podaci se citaju iz .env (vidi .env.example) — nisu u repozitorijumu.
ALLOWED_HOSTS = ['127.0.0.1']

DATABASES = {
    # Za rad nad stvarnom bazom umesto SQLite-a, zameni 'default' sa:
    #     'default': {'ENGINE': 'mssql', **database_credentials()},
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },

    'server_db': {
        'ENGINE': 'mssql',
        **database_credentials(),
    },
}

DATABASES = apply_mssql_connection_defaults(DATABASES)
