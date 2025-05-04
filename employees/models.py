from django.db import models
from django.conf import settings
from django.db.models import Sum
from datetime import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save

class Specialization(models.Model):
    name = models.CharField("Specialization", max_length=100, unique=True)

    def __str__(self):
        return self.name

class ServiceType(models.Model):
    code = models.CharField("Code", max_length=4, unique=True)
    name = models.CharField("Name", max_length=100)

    specializations = models.ManyToManyField(
        Specialization,
        through='ServiceTypeSpecialization',
        related_name='service_types',
        blank=True
    )

    def __str__(self):
        return f"{self.code}"

class ServiceTypeSpecialization(models.Model):
    service_type   = models.ForeignKey(
        ServiceType,
        on_delete=models.CASCADE
    )
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('service_type', 'specialization')

    def __str__(self):
        return f"{self.service_type.code} ↔ {self.specialization.name}"

class EmployeeProfile(models.Model):
    user            = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    specializations = models.ManyToManyField(
        Specialization,
        blank=True,
        help_text="Select one or more specializations for this employee"
    )
    def __str__(self):
        return f"Profile: {self.user.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_employee_profile(sender, instance, created, **kwargs):
    if created:
        EmployeeProfile.objects.create(user=instance)

class Group(models.Model):
    name = models.CharField("Group Name", max_length=100)
    type = models.IntegerField("Type", default=0)
    def __str__(self):
        return self.name

class File(models.Model):
    number       = models.IntegerField("File Number", unique=True)
    patient_name = models.CharField("Patient Name", max_length=100)
    group        = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='files'
    )
    def __str__(self):
        return f"File {self.number} – {self.patient_name} (Group: {self.group.name})"


class PaymentType(models.Model):
    CASH = 'Cash'
    CASH_LIMIT = 45  # days till cash expire

    file           = models.ForeignKey(
        File, on_delete=models.CASCADE, related_name='payment_types'
    )
    service_type   = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name='payment_types'
    )
    insurance      = models.CharField(
        "Insurance", max_length=10,
        choices=[('Thiqa','Thiqa'),('Enhanced','Enhanced'),(CASH,CASH),('Free','Free')]
    )
    num_of_session = models.PositiveIntegerField("Total Sessions", default=10)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def total_sessions(self):
        if self.insurance != self.CASH:
            return None
        agg = PaymentType.objects.filter(
            file=self.file,
            service_type=self.service_type,
            insurance=self.CASH
        ).aggregate(total=Sum('num_of_session'))
        return agg['total'] or 0

    def sessions_used(self):
        return self.employee_records.filter(
            payment_type__file=self.file,
            payment_type__service_type=self.service_type
        ).count()

    def sessions_remaining(self):
        if self.insurance != self.CASH:
            return None
        return self.total_sessions() - self.sessions_used()

    def __str__(self):
        base = f"{self.file} • {self.insurance}/{self.service_type.code}"
        if self.insurance == self.CASH:
            rem = self.sessions_remaining()
            tot = self.total_sessions()
            days_passed = (datetime.now() - self.updated_at).days
            status = "Expired" if days_passed > self.CASH_LIMIT else f"{self.CASH_LIMIT - days_passed}d"
            return f"{base} ({rem}/{tot}) ({status})"
        return f"{base} (Unlimited)"

class EmployeeRecord(models.Model):
    payment_type     = models.ForeignKey(
        PaymentType, on_delete=models.PROTECT, related_name='employee_records'
    )
    location         = models.CharField("Location", max_length=100)
    is_session       = models.BooleanField(
        "Session (True=session, False=follow-up)", default=True
    )
    duration_minutes = models.PositiveIntegerField("Duration (minutes)")
    remarks          = models.TextField("Remarks", blank=True)
    date             = models.DateTimeField("Date of Communication", auto_now_add=True)
    created_by       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_records'
    )
    def __str__(self):
        ts = self.date.strftime('%Y-%m-%d %H:%M')
        return f"{self.payment_type.file} – {self.payment_type.file.patient_name} ({ts})"
