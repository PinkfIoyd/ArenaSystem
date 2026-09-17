class BaseAccessAdapter:
    provider_key = None

    def handle(self, event, access_points):
        raise NotImplementedError


class ManualAccessAdapter(BaseAccessAdapter):
    provider_key = 'manual'

    def handle(self, event, access_points):
        return {'status': 'ignored', 'detail': 'Nenhum equipamento físico configurado.'}


ADAPTERS = {'manual': ManualAccessAdapter()}


def register_access_adapter(adapter):
    if not adapter.provider_key:
        raise ValueError('O adaptador precisa declarar provider_key.')
    ADAPTERS[adapter.provider_key] = adapter


def get_access_adapter(provider_key):
    return ADAPTERS.get(provider_key)
