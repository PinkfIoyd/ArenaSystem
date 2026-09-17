from datetime import time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from aulas.models import Turma
from arena.models import (
    Arena, ArenaBusinessHours, ArenaOnboarding, Matricula, Modalidade,
    PlanAccessWindow, Plano, Quadra,
)
from gestao.models import ReservaQuadra
from loja.models import Categoria, Produto
from saas_billing.models import SaasInvoice, SaasPlan, SaasSubscription
from saas_billing.services import plan_snapshot, sync_legacy_arena, take_daily_snapshot
from saas_ops.models import SupportMessage, SupportTicket
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Cria tres contas SaaS totalmente ficticias para demonstracao comercial.'

    def handle(self, *args, **options):
        if not settings.DEMO_MODE:
            raise CommandError('seed_saas_demo exige DEMO_MODE=True.')
        if not settings.DEMO_ADMIN_PASSWORD:
            raise CommandError('DEMO_ADMIN_PASSWORD deve ser configurada e nao pode estar vazia.')
        try:
            validate_password(settings.DEMO_ADMIN_PASSWORD)
        except ValidationError as exc:
            raise CommandError(f'DEMO_ADMIN_PASSWORD insegura: {" ".join(exc.messages)}') from exc

        plans = self._plans()
        scenarios = [
            ('demo-trial-club', 'Academia Horizonte Demo', 'trialing', plans['starter'], 'academia'),
            ('demo-active-club', 'Arena Oceano Demo', 'active', plans['professional'], 'arena'),
            ('demo-overdue-club', 'Academia Solar Demo', 'suspended', plans['starter'], 'academia'),
        ]
        for slug, name, subscription_status, plan, business_type in scenarios:
            self._arena(slug, name, subscription_status, plan, business_type)
        take_daily_snapshot()
        self.stdout.write(self.style.SUCCESS('Tres arenas SaaS ficticias criadas/atualizadas.'))

    def _plans(self):
        definitions = {
            'starter': ('Starter Demo', '149.00', '1490.00', 150, 4, 3, 10),
            'professional': ('Professional Demo', '299.00', '2990.00', 500, 10, 8, 30),
            'enterprise': ('Enterprise Demo', '599.00', '5990.00', 2000, 30, 20, 100),
        }
        result = {}
        for code, (name, monthly, annual, students, courts, admins, professors) in definitions.items():
            plan, _ = SaasPlan.objects.update_or_create(
                code=code,
                defaults={
                    'name': name, 'description': 'Preco ficticio exclusivo do ambiente de demonstracao.',
                    'published': True, 'monthly_price': Decimal(monthly), 'annual_price': Decimal(annual),
                    'max_students': students, 'max_courts': courts, 'max_admins': admins,
                    'max_professors': professors, 'storage_mb': 1024,
                    'features': {'advanced_reports': code != 'starter', 'integrations': code == 'enterprise'},
                },
            )
            result[code] = plan
        return result

    def _arena(self, slug, name, subscription_status, saas_plan, business_type):
        arena, _ = Arena.objects.update_or_create(
            slug=slug,
            defaults={
                'nome': name, 'tipo_negocio': business_type,
                'email_contato': f'contato@{slug}.example.test',
                'telefone_contato': '+55 21 0000-0000', 'endereco': 'Endereco totalmente ficticio',
                'cor_primaria': '#0F766E', 'cor_secundaria': '#A3E635',
            },
        )
        operational = arena.get_operational_settings()
        defaults = operational.defaults_for(business_type)
        for field, value in defaults.items():
            setattr(operational, field, value)
        operational.save()
        for weekday in range(7):
            ArenaBusinessHours.objects.update_or_create(
                arena=arena, weekday=weekday,
                defaults={'opens_at': time(6, 0), 'closes_at': time(22, 0), 'closed': False},
            )
        now = timezone.now()
        subscription, _ = SaasSubscription.objects.update_or_create(
            arena=arena,
            defaults={
                'plan': saas_plan, 'billing_cycle': 'monthly', 'status': subscription_status,
                'trial_started_at': now - timedelta(days=3),
                'trial_ends_at': now + timedelta(days=11) if subscription_status == 'trialing' else None,
                'current_period_start': now - timedelta(days=10) if subscription_status != 'trialing' else None,
                'current_period_end': now + timedelta(days=20) if subscription_status != 'trialing' else None,
                'grace_ends_at': now - timedelta(days=1) if subscription_status == 'suspended' else None,
            },
        )
        sync_legacy_arena(subscription)
        owner, _ = Usuario.objects.update_or_create(
            username=f'demo.owner.{slug}',
            defaults={
                'email': f'owner@{slug}.example.test', 'first_name': 'Gestor', 'last_name': 'Demo',
                'tipo': 'admin_arena', 'papel': 'dono', 'arena': arena, 'is_staff': True, 'is_active': True,
            },
        )
        owner.set_password(settings.DEMO_ADMIN_PASSWORD)
        owner.save(update_fields=['password'])
        professor, _ = Usuario.objects.update_or_create(
            username=f'demo.prof.{slug}',
            defaults={
                'email': f'professor@{slug}.example.test', 'first_name': 'Professor', 'last_name': 'Demo',
                'tipo': 'professor', 'papel': 'professor', 'arena': arena, 'is_active': True,
            },
        )
        professor.set_password(settings.DEMO_ADMIN_PASSWORD)
        professor.save(update_fields=['password'])
        student, _ = Usuario.objects.update_or_create(
            username=f'demo.student.{slug}',
            defaults={
                'email': f'aluno@{slug}.example.test', 'first_name': 'Aluno', 'last_name': 'Demo',
                'tipo': 'aluno', 'papel': 'aluno', 'arena': arena, 'is_active': True,
            },
        )
        student.set_password(settings.DEMO_ADMIN_PASSWORD)
        student.save(update_fields=['password'])

        court, _ = Quadra.objects.update_or_create(
            arena=arena, nome='Espaco Demo 1' if business_type == 'academia' else 'Quadra Demo 1',
            defaults={
                'tipo_espaco': 'gym_floor' if business_type == 'academia' else 'court',
                'tipo_areia': '' if business_type == 'academia' else 'Areia clara', 'ativa': True,
            },
        )
        modality, _ = Modalidade.objects.update_or_create(
            arena=arena, nome='Beach Tennis Demo', defaults={'cor': '#0F766E', 'ativa': True},
        )
        turma, _ = Turma.objects.update_or_create(
            arena=arena, nome='Turma Demo Noturna',
            defaults={
                'professor': professor, 'quadra': court, 'modalidade': modality,
                'dias_semana': 'seg,qua', 'horario': time(19, 0), 'vagas': 8, 'ativa': True,
            },
        )
        turma.alunos.add(student)
        student_plan, _ = Plano.objects.update_or_create(
            arena=arena, nome='Mensal Demo', defaults={
                'valor': Decimal('250.00'), 'frequencia_semanal': 2,
                'tipo_acesso': 'hybrid' if business_type == 'academia' else 'classes_only',
                'ativo': True,
            },
        )
        if business_type == 'academia':
            for weekday in range(7):
                PlanAccessWindow.objects.update_or_create(
                    plano=student_plan, weekday=weekday, starts_at=time(6), ends_at=time(22),
                )
        Matricula.objects.update_or_create(
            arena=arena, aluno=student, plano=student_plan,
            defaults={'data_inicio': timezone.localdate() - timedelta(days=30), 'ativa': True},
        )
        category, _ = Categoria.objects.get_or_create(arena=arena, nome='Bebidas Demo')
        Produto.objects.update_or_create(
            arena=arena, sku=f'DEMO-{arena.id}-AGUA',
            defaults={'categoria': category, 'nome': 'Agua Demo', 'preco': Decimal('6.00'), 'estoque': 4, 'estoque_minimo': 5, 'ativo': True},
        )
        ReservaQuadra.objects.update_or_create(
            arena=arena, quadra=court, data=timezone.localdate() + timedelta(days=1),
            hora_inicio=time(18, 0), hora_fim=time(19, 0),
            defaults={
                'aluno': student, 'cliente_nome': 'Aluno Demo', 'cliente_telefone': '',
                'valor': Decimal('120.00'), 'status': 'confirmada',
                'observacoes': 'Reserva totalmente ficticia.', 'criado_por': owner,
            },
        )
        onboarding, _ = ArenaOnboarding.objects.get_or_create(arena=arena)
        if subscription_status == 'trialing':
            onboarding.completed_steps = ['identification', 'courts']
            onboarding.current_step = 'hours'
            onboarding.completed_at = None
        else:
            onboarding.completed_steps = ['identification', 'hours', 'courts', 'modalities', 'professors', 'students', 'review']
            onboarding.current_step = 'review'
            onboarding.completed_at = now
        onboarding.save(update_fields=['completed_steps', 'current_step', 'completed_at', 'updated_at'])

        invoice_status = 'paid' if subscription_status == 'active' else 'failed' if subscription_status == 'suspended' else 'pending'
        invoice, _ = SaasInvoice.objects.update_or_create(
            external_reference=f'saas-demo:{slug}:2026-08',
            defaults={
                'arena': arena, 'subscription': subscription, 'kind': 'subscription',
                'status': invoice_status, 'amount': saas_plan.monthly_price,
                'paid_at': now - timedelta(days=10) if invoice_status == 'paid' else None,
                'plan_snapshot': plan_snapshot(saas_plan),
            },
        )
        ticket, _ = SupportTicket.objects.get_or_create(
            arena=arena, subject='Chamado ficticio de boas-vindas',
            defaults={'category': 'onboarding', 'priority': 'normal', 'created_by': owner},
        )
        SupportMessage.objects.get_or_create(
            ticket=ticket, author=owner, body='Mensagem ficticia para demonstrar o atendimento.', defaults={'internal': False},
        )
