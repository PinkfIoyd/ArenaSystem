import json
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils.text import slugify


class MercadoPagoConfigError(Exception):
    pass


class MercadoPagoAPIError(Exception):
    pass


def criar_dados_iniciais_arena(arena, dados_admin=None):
    from arena.models import Plano, Quadra
    from loja.models import Categoria
    from usuarios.models import Usuario

    Quadra.objects.get_or_create(
        arena=arena,
        nome='Quadra 1',
        defaults={'tipo_areia': 'Areia', 'ativa': True, 'observacoes': 'Quadra inicial criada automaticamente.'},
    )
    Plano.objects.get_or_create(
        arena=arena,
        nome='Mensal 2x semana',
        defaults={'valor': 290, 'frequencia_semanal': 2, 'descricao': 'Plano inicial sugerido.', 'ativo': True},
    )
    Plano.objects.get_or_create(
        arena=arena,
        nome='Livre modalidades',
        defaults={'valor': 420, 'frequencia_semanal': 4, 'descricao': 'Plano inicial sugerido.', 'ativo': True},
    )
    for categoria in ['Bebidas', 'Comidas', 'Uniforme', 'Bola', 'Vestuario']:
        Categoria.objects.get_or_create(arena=arena, nome=categoria)

    dados_admin = dados_admin or {}
    email = dados_admin.get('admin_email') or arena.email_contato
    if email and not Usuario.objects.filter(arena=arena, email=email).exists():
        username_base = slugify(email.split('@')[0]) or f'admin-{arena.slug}'
        username = username_base
        contador = 1
        while Usuario.objects.filter(username=username).exists():
            contador += 1
            username = f'{username_base}{contador}'
        admin = Usuario.objects.create_user(
            username=username,
            email=email,
            first_name=dados_admin.get('admin_nome', 'Admin'),
            last_name=dados_admin.get('admin_sobrenome', arena.nome),
            tipo='admin_arena',
            papel='dono',
            arena=arena,
            is_staff=True,
        )
        senha = dados_admin.get('admin_senha') or secrets.token_urlsafe(9)
        admin.set_password(senha)
        admin.save(update_fields=['password'])
        admin._senha_temporaria = senha
        return admin
    return None


def _access_token():
    token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', '')
    if not token:
        raise MercadoPagoConfigError('Configure MERCADO_PAGO_ACCESS_TOKEN no .env.')
    return token


def _request_json(method, url, payload=None):
    headers = {
        'Authorization': f'Bearer {_access_token()}',
        'Content-Type': 'application/json',
    }
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    request = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        detalhe = exc.read().decode('utf-8', errors='ignore')
        raise MercadoPagoAPIError(f'Mercado Pago retornou {exc.code}: {detalhe}') from exc
    except URLError as exc:
        raise MercadoPagoAPIError(f'Erro ao conectar ao Mercado Pago: {exc.reason}') from exc


def criar_preferencia_mensalidade(mensalidade):
    aluno = mensalidade.matricula.aluno
    external_reference = mensalidade.external_reference or f'mensalidade:{mensalidade.id}'

    payload = {
        'items': [
            {
                'id': str(mensalidade.id),
                'title': f'Mensalidade {mensalidade.mes_referencia:%m/%Y}',
                'description': mensalidade.plano_nome if hasattr(mensalidade, 'plano_nome') else mensalidade.matricula.plano.nome,
                'quantity': 1,
                'currency_id': 'BRL',
                'unit_price': float(mensalidade.valor),
            }
        ],
        'payer': {
            'name': aluno.first_name,
            'surname': aluno.last_name,
            'email': aluno.email,
        },
        'back_urls': {
            'success': f'{settings.FRONTEND_URL}/mensalidades',
            'pending': f'{settings.FRONTEND_URL}/mensalidades',
            'failure': f'{settings.FRONTEND_URL}/mensalidades',
        },
        'notification_url': f'{settings.PUBLIC_BACKEND_URL}/api/mercado-pago/webhook/',
        'external_reference': external_reference,
        'auto_return': 'approved',
        'payment_methods': {
            'installments': 1,
        },
    }

    preference = _request_json(
        'POST',
        'https://api.mercadopago.com/checkout/preferences',
        payload,
    )

    mensalidade.external_reference = external_reference
    mensalidade.mercado_pago_preference_id = preference.get('id', '')
    mensalidade.mercado_pago_checkout_url = (
        preference.get('init_point')
        or preference.get('sandbox_init_point')
        or ''
    )
    mensalidade.save(update_fields=[
        'external_reference',
        'mercado_pago_preference_id',
        'mercado_pago_checkout_url',
    ])
    return mensalidade.mercado_pago_checkout_url


def obter_pagamento(payment_id):
    return _request_json('GET', f'https://api.mercadopago.com/v1/payments/{payment_id}')


def buscar_pagamentos_por_referencia(external_reference):
    query = urlencode({'external_reference': external_reference})
    return _request_json('GET', f'https://api.mercadopago.com/v1/payments/search?{query}')
