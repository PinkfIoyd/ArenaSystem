from rest_framework.exceptions import APIException


class PaymentRequired(APIException):
    status_code = 402
    default_code = 'subscription_inactive'
    default_detail = 'A assinatura da arena nao permite esta operacao.'


class PlanLimitReached(APIException):
    status_code = 409
    default_code = 'plan_limit_reached'

    def __init__(self, resource, usage, limit):
        super().__init__({
            'code': self.default_code,
            'detail': 'O limite contratado foi atingido.',
            'resource': resource,
            'usage': usage,
            'limit': limit,
            'action': 'Revise o consumo ou altere o plano em Minha assinatura.',
        })

