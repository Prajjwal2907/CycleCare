from decouple import config

env = config('DJANGO_ENV', default='dev').lower()

if env in ('prod', 'production'):
    from .prod import *
else:
    from .dev import *
