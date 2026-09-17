from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    scope = 'auth_login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class RegisterRateThrottle(SimpleRateThrottle):
    scope = 'auth_register'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class AccountSecurityRateThrottle(SimpleRateThrottle):
    scope = 'account_security'

    def get_cache_key(self, request, view):
        ident = str(request.user.pk) if request.user and request.user.is_authenticated else self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}
