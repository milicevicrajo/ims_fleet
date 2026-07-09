from .base import * 

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
        'NAME': 'IMS_ERP',  # Naziv baze na serveru
        'USER': 'Rajo Milicevic',
        'PASSWORD': 'Rajo123',
        'HOST': 'SMS-SERVER',
        'PORT': '',  # Ostavite prazno ako koristite podrazumevani port
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    },

    'local': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },

    'server_db': {
        'ENGINE': 'mssql',
        'NAME': 'IMS_ERP',  # Naziv baze na serveru
        'USER': 'Rajo Milicevic',
        'PASSWORD': 'Rajo123',
        'HOST': 'SMS-SERVER',
        'PORT': '',  # Ostavite prazno ako koristite podrazumevani port
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    },
}

DATABASES = apply_mssql_connection_defaults(DATABASES)
