# Generated manually for trainer reverse-relation tasks

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trainer', '0002_blegroup_bleroute_company_constructionsite_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shelf',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100, verbose_name='Метка полки')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainer.book')),
            ],
            options={
                'verbose_name': 'Полка',
                'verbose_name_plural': 'Полки',
            },
        ),
    ]
