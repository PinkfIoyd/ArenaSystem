from .settings import *  # noqa: F403,F401


# Configuração equivalente à produção para validação local. Não deve ser usada
# para servir tráfego; mantém SQLite apenas para permitir `check --deploy`
# sem depender de credenciais externas.
DEBUG = False
SECRET_KEY = 'deploy-check-local-only-J7u!4xQ9@bL2#nT8$vK5%rM1&cP6*zS3'
ALLOWED_HOSTS = ['example.test']
CORS_ALLOWED_ORIGINS = ['https://example.test']
CSRF_TRUSTED_ORIGINS = ['https://example.test']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
