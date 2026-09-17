from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0005_mensalidade_external_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arena',
            name='cor_primaria',
            field=models.CharField(default='#0F766E', max_length=20),
        ),
        migrations.AlterField(
            model_name='arena',
            name='cor_secundaria',
            field=models.CharField(default='#A3E635', max_length=20),
        ),
        migrations.AlterField(
            model_name='arena',
            name='cor_fundo',
            field=models.CharField(default='#ECFEFF', max_length=20),
        ),
        migrations.AlterField(
            model_name='arena',
            name='cor_texto',
            field=models.CharField(default='#071B26', max_length=20),
        ),
    ]
