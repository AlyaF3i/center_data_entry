import os
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from employees.models import Specialization, ServiceType
from django.conf import settings

class Command(BaseCommand):
    help = "Load specializations and therapists from JSON files"

    def handle(self, *args, **kwargs):
        base_dir = settings.BASE_DIR
        data_dir = os.path.join(base_dir, 'data')

        spec_path = os.path.join(data_dir, 'specialization.json')
        therapist_path = os.path.join(data_dir, 'therapists.json')

        # Load specialization mapping
        with open(spec_path, 'r', encoding='utf-8') as f:
            specialization_map = json.load(f)

        # Step 1: Create Specializations and ServiceTypes
        for spec_key, code in specialization_map.items():
            specialization, _ = Specialization.objects.get_or_create(name=spec_key)

            service_type, created = ServiceType.objects.get_or_create(
                code=code,
                defaults={'name': f"{spec_key.replace('_', ' ').title()}"}
            )

            service_type.specializations.add(specialization)

            self.stdout.write(self.style.SUCCESS(f"✔ Created/linked ServiceType '{code}' to Specialization '{spec_key}'"))

        # Load therapists
        with open(therapist_path, 'r', encoding='utf-8') as f:
            therapist_data = json.load(f)

        # Step 2: Create users and link to Specializations
        for group_key, users in therapist_data.items():
            specialization = Specialization.objects.filter(name=group_key).first()
            if not specialization:
                self.stdout.write(self.style.WARNING(f"⚠ Skipping {group_key} (Specialization not found)"))
                continue

            for user_data in users:
                username = user_data['username']
                password = user_data['password']
                full_name = user_data['fullName']

                if User.objects.filter(username=username).exists():
                    self.stdout.write(f"⏭ User '{username}' already exists. Skipping.")
                    continue

                first_name, *last_name = full_name.split()
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=' '.join(last_name)
                )

                # Link user to specialization via profile
                profile = user.employee_profile
                profile.specializations.add(specialization)

                self.stdout.write(self.style.SUCCESS(f"✔ Created user '{username}' and linked to '{group_key}'"))

        self.stdout.write(self.style.SUCCESS("🎉 All data loaded successfully."))
