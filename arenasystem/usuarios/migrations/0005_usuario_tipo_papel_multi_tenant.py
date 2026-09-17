from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_alter_usuario_foto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='papel',
            field=models.CharField(blank=True, choices=[('superadmin_saas', 'Superadmin SaaS'), ('dono', 'Dono'), ('recepcao', 'Recepcao'), ('financeiro', 'Financeiro'), ('professor', 'Professor'), ('estoque', 'Estoque'), ('aluno', 'Aluno')], max_length=20),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='tipo',
            field=models.CharField(choices=[('aluno', 'Aluno'), ('professor', 'Professor'), ('admin', 'Administrador'), ('admin_arena', 'Administrador da arena'), ('funcionario', 'Funcionario'), ('superadmin_saas', 'Superadmin SaaS')], default='aluno', max_length=20),
        ),
    ]
