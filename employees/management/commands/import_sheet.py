import pandas as pd
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from employees.models import Group, File, PaymentType

User = get_user_model()

GROUP_NAMES = ['Center', 'Almadar', "Teddy'S Inn", 'Aldana', 'Alsomow', 'Alshiam ', 'Little Regent', 'Belvedere British', 'Manor Hall International ', 'Bedaya Center']

class Command(BaseCommand):
    help = "Create superadmin, groups, then import Files & PaymentTypes linked by LOCATION"

    def add_arguments(self, parser):
        parser.add_argument('path',  type=str, help="Excel file path")
        parser.add_argument('sheet', type=str, help="Sheet name in the workbook")

    def handle(self, *args, **options):
        # 1) Ensure superuser 'admin'/'admin'
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin', first_name = "Rama", last_name = "Alkhobbi")
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' created."))

        # 2) Create/ensure Groups (capitalized names)
        groups = {}
        for raw in GROUP_NAMES:
            name = raw.strip().title()
            grp, _ = Group.objects.get_or_create(name=name, defaults={'type': 0})
            groups[name] = grp
        self.stdout.write(self.style.SUCCESS(f"Ensured {len(groups)} groups."))

        # 3) Read Excel and import
        df = pd.read_excel(options['path'], sheet_name=options['sheet'])
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Importing rows"):
            file_num     = int(row['FILE'])
            service_type = str(row['TRX']).strip()
            insurance    = str(row['COMP']).strip()
            patient_name = str(row['NAME']).strip().title()
            loc_raw      = str(row['LOCATION']).strip().title()

            # Default to Center if LOCATION not recognised
            group = groups.get(loc_raw, groups['Center'])

            # Create or update File
            file_obj, created = File.objects.get_or_create(
                number=file_num,
                defaults={'patient_name': patient_name, 'group': group}
            )
            if not created:
                if file_obj.patient_name != patient_name or file_obj.group != group:
                    file_obj.patient_name = patient_name
                    file_obj.group        = group
                    file_obj.save()

            # Create or get PaymentType (no dup per file/service/insurance)
            PaymentType.objects.get_or_create(
                file=file_obj,
                service_type=service_type,
                insurance=insurance,
                defaults={'num_of_session': 10}
            )

        self.stdout.write(self.style.SUCCESS("Import completed successfully."))
