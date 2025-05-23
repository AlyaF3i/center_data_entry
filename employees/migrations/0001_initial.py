# Generated by Django 5.0.4 on 2025-05-02 20:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Group Name')),
                ('type', models.IntegerField(default=0, verbose_name='Type')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=4, unique=True, verbose_name='Code')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
            ],
        ),
        migrations.CreateModel(
            name='Specialization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Specialization')),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(unique=True, verbose_name='File Number')),
                ('patient_name', models.CharField(max_length=100, verbose_name='Patient Name')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='employees.group')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('insurance', models.CharField(choices=[('Thiqa', 'Thiqa'), ('Enhanced', 'Enhanced'), ('Cash', 'Cash'), ('Free', 'Free')], max_length=10, verbose_name='Insurance')),
                ('num_of_session', models.PositiveIntegerField(default=10, verbose_name='Total Sessions')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_types', to='employees.file')),
                ('service_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payment_types', to='employees.servicetype')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=100, verbose_name='Location')),
                ('is_session', models.BooleanField(default=True, verbose_name='Session (True=session, False=follow-up)')),
                ('duration_minutes', models.PositiveIntegerField(verbose_name='Duration (minutes)')),
                ('remarks', models.TextField(blank=True, verbose_name='Remarks')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date of Communication')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_records', to=settings.AUTH_USER_MODEL)),
                ('payment_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employee_records', to='employees.paymenttype')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceTypeSpecialization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.servicetype')),
                ('specialization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.specialization')),
            ],
            options={
                'unique_together': {('service_type', 'specialization')},
            },
        ),
        migrations.AddField(
            model_name='servicetype',
            name='specializations',
            field=models.ManyToManyField(blank=True, related_name='service_types', through='employees.ServiceTypeSpecialization', to='employees.specialization'),
        ),
        migrations.CreateModel(
            name='EmployeeProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_profile', to=settings.AUTH_USER_MODEL)),
                ('specializations', models.ManyToManyField(blank=True, help_text='Select one or more specializations for this employee', to='employees.specialization')),
            ],
        ),
    ]
