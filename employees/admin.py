from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Group,
    File,
    ServiceType,
    ServiceTypeSpecialization,
    PaymentType,
    EmployeeRecord,
    Specialization,
    EmployeeProfile,
)

User = get_user_model()


# Inline for the ServiceType↔Specialization through-model
class ServiceTypeSpecializationInline(admin.TabularInline):
    model = ServiceTypeSpecialization
    extra = 1
    # when in ServiceTypeAdmin, Django will infer fk_name='service_type'
    # when in SpecializationAdmin, we’ll override fk_name below


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ('name', 'type')
    list_filter   = ('type',)
    search_fields = ('name',)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display  = ('number', 'patient_name', 'group')
    list_filter   = ('group',)
    search_fields = ('number', 'patient_name',)


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display    = ('code', 'name')
    search_fields   = ('code', 'name')
    inlines         = [ServiceTypeSpecializationInline]  # show Specializations here
    # removed filter_horizontal since we use an explicit through-model


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display    = ('name',)
    search_fields   = ('name',)
    inlines         = [
        type(
            'SpecializationServiceTypeInline',
            (admin.TabularInline,),
            {
                'model': ServiceTypeSpecialization,
                'fk_name': 'specialization',
                'extra': 1
            }
        )
    ]
    # also no filter_horizontal here


@admin.register(ServiceTypeSpecialization)
class ServiceTypeSpecializationAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'specialization')
    list_filter  = ('service_type', 'specialization')


@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display    = (
        'file', 'service_type', 'insurance',
        'num_of_session', 'sessions_used', 'sessions_remaining'
    )
    list_filter     = ('file__group', 'service_type__code', 'insurance')
    search_fields   = ('file__number',)
    ordering        = ('-created_at',)


@admin.register(EmployeeRecord)
class EmployeeRecordAdmin(admin.ModelAdmin):
    list_display    = (
        'payment_type', 'location', 'is_session',
        'duration_minutes', 'date', 'created_by'
    )
    list_filter     = (
        'payment_type__service_type__code',
        'payment_type__insurance',
        'payment_type__file',
        'location',
        'is_session',
        'created_by',
    )
    search_fields   = (
        'payment_type__file__number',
        'location',
        'created_by__username',
    )
    date_hierarchy  = 'date'
    ordering        = ('-date',)


class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    filter_horizontal = ('specializations',)
    verbose_name = "Employee Profile"


class UserAdmin(BaseUserAdmin):
    inlines       = (EmployeeProfileInline,)
    list_display  = BaseUserAdmin.list_display + ('get_specializations',)

    def get_specializations(self, obj):
        return ", ".join(
            s.name for s in obj.employee_profile.specializations.all()
        )
    get_specializations.short_description = "Specializations"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
