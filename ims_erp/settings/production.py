from .base import *


# Pristupni podaci se citaju iz .env (vidi .env.example) — nisu u repozitorijumu.
ALLOWED_HOSTS = [
    "ims-flota",
    "ims.portal",
    "192.168.6.7",
    "127.0.0.1",
    "localhost",
]

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        **database_credentials(),
    },

    'local': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },

    'server_db': {
        'ENGINE': 'mssql',
        **database_credentials(),
    },
}

DATABASES = apply_mssql_connection_defaults(DATABASES)
