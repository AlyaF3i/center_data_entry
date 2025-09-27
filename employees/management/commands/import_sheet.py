# employees/management/commands/import_sheet.py

import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from employees.models import (
    Center,
    Group,
    File,
    ServiceType,
    PaymentType,
    Specialization,
)

User = get_user_model()

# GROUP_NAMES = [
#     'Center', 'Almadar', "Teddy'S Inn", 'Aldana', 'Alsomow',
#     'Alshiam', 'Little Regent', 'Belvedere British',
#     'Manor Hall International', 'Bedaya Center'
# ]


class Command(BaseCommand):
    help = "Ensure admin, General spec, Centers/Groups, then import Files/Services/Payments"

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help="Excel file path")
        parser.add_argument('sheet', type=str, help="Sheet name")
        parser.add_argument('center', type=str, help="Center name")

    def handle(self, *args, **options):
        # 0) Create or get General specialization
        center_name = options['center'].strip().title()
        center_object, _ = Center.objects.get_or_create(name=center_name)
        general_spec, _ = Specialization.objects.get_or_create(name="General")
        self.stdout.write(self.style.SUCCESS("Ensured specialization: General"))

        # 1) Create admin/admin and assign General
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com'}
        )
        
        if created:
            admin.set_password('admin')
            admin.is_superuser = True
            admin.is_staff = True
            admin.first_name = "Rama"
            admin.last_name = "Alkhobbi"
            admin.save()
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' created."))
        # ensure profile exists and add General
        admin.employee_profile.specializations.add(general_spec)
        self.stdout.write(self.style.SUCCESS("Assigned 'General' to admin."))

        # 2) Ensure Centers and Groups
        df = pd.read_excel(options['path'], sheet_name=options['sheet'])
        GROUP_NAMES =  list(set(a for a in df['LOCATION'].values.tolist()))
        groups = {}
        for raw in GROUP_NAMES:
            name = raw.strip().title()
            grp= Group.objects.create(
                name=name,
                center=  center_object
            )
            groups[name] = grp
        self.stdout.write(self.style.SUCCESS(f"Ensured {len(groups)} groups."))

        # 3) Read Excel
        for _, row in df.iterrows():
            file_num = int(row['FILE'])
            trx_code = str(row['TRX']).strip().upper()
            insurance = str(row['COMP']).strip().capitalize()
            patient_name = str(row['NAME']).strip()
            loc_raw = str(row['LOCATION']).strip().title()

            group = groups.get(loc_raw)
            if not group:
                group, _ = Group.objects.get(
                    name=loc_raw,
                    center=center_object,
                    defaults={'type': 0}

                )
                groups[loc_raw] = group

            # File
            fobj, created = File.objects.get_or_create(
                number=file_num,
                defaults={
                    'patient_name': patient_name,
                    'group': group
                }
            )
            updates = {}
            if not created:
                if fobj.patient_name != patient_name:
                    updates['patient_name'] = patient_name
                if fobj.group_id != group.id:
                    updates['group'] = group
                if updates:
                    for field, value in updates.items():
                        setattr(fobj, field, value)
                    fobj.save(update_fields=list(updates.keys()))

            # ServiceType
            stobj, _ = ServiceType.objects.get_or_create(
                code=trx_code,
                defaults={'name': trx_code}
            )

            # ensure General is linked to every service
            stobj.specializations.add(general_spec)

            # PaymentType
            PaymentType.objects.get_or_create(
                file=fobj,
                service_type=stobj,
                insurance=insurance,
                defaults={'num_of_session': 10}
            )

        self.stdout.write(self.style.SUCCESS("Import completed."))
