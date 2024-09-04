from .base import * 

ALLOWED_HOSTS = ['192.168.6.7', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'Vozila_Django',  # Naziv baze na serveru
        'USER': 'Rajo Milicevic',
        'PASSWORD': 'Rajo123',
        'HOST': 'SMS-SERVER',
        'PORT': '',  # Ostavite prazno ako koristite podrazumevani port
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    },
}