from .base import * 


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
ALLOWED_HOSTS = ['127.0.0.1']
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

    'test_db': {
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
