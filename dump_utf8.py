import os
import django

# Postavi varijablu okruženja za Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_fleet.settings')  # Zamenite 'ims_fleet' sa vašim imenom projekta

# Inicijalizuj Django
django.setup()

import sys
import io
from django.core.management import call_command

# Podesi stdout na utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Pozovi dumpdata komandu sa ispravnim kodiranjem
with open('dumpdata.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', stdout=f, indent=4)
