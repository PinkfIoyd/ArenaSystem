from django.db import migrations


def create_drafts(apps, schema_editor):
    LegalDocumentVersion = apps.get_model('saas_ops', 'LegalDocumentVersion')
    for document_type, title in (
        ('terms', 'Termos de uso'),
        ('privacy', 'Politica de privacidade'),
        ('dpa', 'Acordo de tratamento de dados'),
    ):
        LegalDocumentVersion.objects.get_or_create(
            document_type=document_type,
            version='draft-1',
            defaults={
                'title': f'{title} — revisao juridica pendente',
                'content': 'RASCUNHO. Este documento depende de revisao e aprovacao juridica antes da publicacao.',
                'status': 'draft',
            },
        )


class Migration(migrations.Migration):
    dependencies = [('saas_ops', '0001_initial')]
    operations = [migrations.RunPython(create_drafts, migrations.RunPython.noop)]

