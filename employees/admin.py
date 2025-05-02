from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import File, PaymentType, EmployeeRecord, Group, Specialization, EmployeeProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()

class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    verbose_name = "Employee Profile"
    fk_name = 'user'
    filter_horizontal = ('specializations',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ('name', 'type')
    list_filter   = ('type',)
    search_fields = ('name',)

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display  = ('number', 'patient_name', 'group')
    list_filter   = ('group',)
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

class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeProfileInline,)
    list_display = BaseUserAdmin.list_display + ('get_specializations',)
    def get_specializations(self, obj):
        return ", ".join(s.name for s in obj.employee_profile.specializations.all())
    get_specializations.short_description = "Specializations"

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display  = ('name',)
    search_fields = ('name',)