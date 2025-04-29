from django.contrib import admin
from .models import File, PaymentType, EmployeeRecord

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display  = ('number', 'patient_name')
    search_fields = ('number', 'patient_name')

@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display   = (
        'file', 'service_type', 'insurance',
        'num_of_session', 'sessions_used', 'sessions_remaining',
        'created_at', 'updated_at'
    )
    list_filter    = ('file', 'service_type', 'insurance')
    search_fields  = ('file__number',)
    ordering       = ('-created_at',)

@admin.register(EmployeeRecord)
class EmployeeRecordAdmin(admin.ModelAdmin):
    list_display   = (
        'payment_type', 'location', 'is_session',
        'duration_minutes',
        'date', 'created_by'
    )
    list_filter    = (
        'payment_type__service_type',
        'payment_type__insurance',
        'payment_type__file',
        'location',
        'is_session',
        'created_by',
    )
    search_fields  = (
        'payment_type__file__number',
        'location',
        'created_by__username',
    )
    date_hierarchy = 'date'
    ordering       = ('-date',)
