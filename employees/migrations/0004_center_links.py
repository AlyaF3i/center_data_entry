from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_paymenttypecanceled_file_created_at_file_updated_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Center',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='Center Name')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is Active')),
            ],
        ),
        migrations.AddField(
            model_name='group',
            name='center',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='groups', to='employees.center', verbose_name='Center'),
        ),
        migrations.AddField(
            model_name='file',
            name='center',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='files', to='employees.center', verbose_name='Center'),
        ),
    ]
