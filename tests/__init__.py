import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "revdesign.settings")

import django
django.setup()

from django.core.management import call_command