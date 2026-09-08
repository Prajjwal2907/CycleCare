import urllib.parse
from .base import *

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True

db_url = config('DATABASE_URL', default=None)
if db_url and (db_url.startswith('postgres://') or db_url.startswith('postgresql://')):
    url = urllib.parse.urlparse(db_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path.lstrip('/'),
            'USER': url.username or '',
            'PASSWORD': url.password or '',
            'HOST': url.hostname or 'localhost',
            'PORT': url.port or 5432,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
