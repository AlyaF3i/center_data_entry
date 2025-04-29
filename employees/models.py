from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

class File(models.Model):
    number       = models.IntegerField("File Number", unique=True)
    patient_name = models.CharField("Patient Name", max_length=100)

    def __str__(self):
        return f"File {self.number} – {self.patient_name}"


class PaymentType(models.Model):
    CASH = 'Cash'

    CASH_LIMIT = 45 # days till cash expire
    
    file           = models.ForeignKey(
        File, on_delete=models.CASCADE, related_name='payment_types'
    )
    service_type   = models.CharField(
        "Service Type", max_length=4,
        choices=[('OT','OT'),('ST','ST'),('SE','SE'),('BEH','BEH'),('PT','PT')]
    )
    insurance      = models.CharField(
        "Insurance", max_length=10,
        choices=[('Thiqa','Thiqa'),('Enhanced','Enhanced'),(CASH,CASH),('Free','Free')]
    )
    num_of_session = models.PositiveIntegerField("Total Sessions", default=10)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def total_sessions(self):
        # Only sum limits for Cash
        if self.insurance != self.CASH:
            return None
        agg = PaymentType.objects.filter(
            file=self.file,
            service_type=self.service_type,
            insurance=self.CASH
        ).aggregate(total=Sum('num_of_session'))
        return agg['total'] or 0

    def sessions_used(self):
        # Count all records under this file+service (regardless of insurance)
        return self.employee_records.filter(
            payment_type__file=self.file,
            payment_type__service_type=self.service_type
        ).count()

    def sessions_remaining(self):
        if self.insurance != self.CASH:
            return None
        return self.total_sessions() - self.sessions_used()

    def __str__(self):
        # Cash shows counts; others show "Unlimited"
        if self.insurance == self.CASH:
            rem = self.sessions_remaining()
            tot = self.total_sessions()
            days_passed = (timezone.now() - self.updated_at).days
            if days_passed > self.CASH_LIMIT:
                status = "Expired"
            else:
                status = f"{self.CASH_LIMIT - days_passed}d"
            return f"{self.file} • {self.insurance}/{self.service_type} ({rem}/{tot}) ({status})"
        return f"{self.file} • {self.insurance}/{self.service_type} (Unlimited)"


class EmployeeRecord(models.Model):
    payment_type     = models.ForeignKey(
        PaymentType, on_delete=models.PROTECT, related_name='employee_records'
    )
    location         = models.CharField("Location", max_length=100)
    is_session       = models.BooleanField(
        "Session (True=session, False=follow-up)", default=True
    )
    # patient_name     = models.CharField("Patient Name", max_length=100)
    duration_minutes = models.PositiveIntegerField("Duration (minutes)")
    remarks          = models.TextField("Remarks", blank=True)
    date             = models.DateTimeField(
        "Date of Communication", auto_now_add=True
    )
    created_by       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_records'
    )

    def __str__(self):
        ts = self.date.strftime('%Y-%m-%d %H:%M')
        return f"{self.payment_type.file} – {self.payment_type.file.patient_name} ({ts})"
