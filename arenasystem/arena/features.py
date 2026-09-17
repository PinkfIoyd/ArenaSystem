from rest_framework.exceptions import PermissionDenied

from .tenant import get_user_arena


FEATURE_FIELDS = {
    'classes': 'classes_enabled',
    'open_access': 'open_access_enabled',
    'reservations': 'reservations_enabled',
    'store': 'store_enabled',
}


def assert_feature_enabled(arena, feature):
    field = FEATURE_FIELDS[feature]
    if not getattr(arena.get_operational_settings(), field):
        raise PermissionDenied({'code': 'feature_disabled', 'detail': 'Este módulo está desabilitado nesta unidade.', 'feature': feature})


class FeatureEnabledMixin:
    feature_key = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user and request.user.is_authenticated and self.feature_key:
            assert_feature_enabled(get_user_arena(request.user), self.feature_key)
