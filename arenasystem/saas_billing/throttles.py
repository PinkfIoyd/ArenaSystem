from rest_framework.throttling import SimpleRateThrottle


class SaasWebhookThrottle(SimpleRateThrottle):
    scope = 'saas_webhook'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}

