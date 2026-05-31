from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Center,
    Group,
    File,
    ServiceType,
    ServiceTypeSpecialization,
    PaymentType,
    EmployeeRecord,
    Specialization,
    EmployeeProfile,
    PaymentTypeCanceled,
)
import base64
import os
from django.urls import path
from django.conf import settings
from django.http import FileResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from rangefilter.filters import DateRangeFilter

User = get_user_model()


class MultiSelectListFilter(admin.SimpleListFilter):
    """Admin sidebar filter that allows several values in one query parameter."""

    field_path = None
    extra_remove_parameters = ()

    def encode_value(self, value):
        raw_value = str(value).encode('utf-8')
        return base64.urlsafe_b64encode(raw_value).decode('ascii').rstrip('=')

    def decode_value(self, value):
        padding = '=' * (-len(value) % 4)
        return base64.urlsafe_b64decode(f'{value}{padding}').decode('utf-8')

    def token_list(self):
        value = self.value()
        if not value:
            return []
        return [item for item in value.split(',') if item]

    def value_list(self):
        return [self.decode_value(token) for token in self.token_list()]

    def queryset(self, request, queryset):
        values = self.value_list()
        if not values:
            return queryset
        return queryset.filter(**{f'{self.field_path}__in': values})

    def remove_parameters(self):
        return [
            self.parameter_name,
            self.field_path,
            f'{self.field_path}__exact',
            f'{self.field_path}__id__exact',
            *self.extra_remove_parameters,
        ]

    def choices(self, changelist):
        selected = set(self.token_list())
        yield {
            'selected': not selected,
            'query_string': changelist.get_query_string(remove=self.remove_parameters()),
            'display': 'All',
        }

        for lookup, title in self.lookup_choices:
            lookup = self.encode_value(lookup)
            next_selected = set(selected)
            if lookup in next_selected:
                next_selected.remove(lookup)
            else:
                next_selected.add(lookup)

            if next_selected:
                query_string = changelist.get_query_string({
                    self.parameter_name: ','.join(sorted(next_selected)),
                }, remove=self.remove_parameters())
            else:
                query_string = changelist.get_query_string(remove=self.remove_parameters())

            yield {
                'selected': lookup in selected,
                'query_string': query_string,
                'display': title,
            }


class PaymentTypeMultiSelectFilter(MultiSelectListFilter):
    title = 'payment type'
    parameter_name = 'payment_type_multi'
    field_path = 'payment_type'

    def lookups(self, request, model_admin):
        payment_types = (
            PaymentType.objects
            .filter(employee_records__isnull=False)
            .select_related('file', 'service_type', 'file__group__center', 'file__group')
            .distinct()
            .order_by('file__number', 'insurance', 'service_type__code')
        )
        return [
            (payment_type.pk, (
                f'{payment_type.file.number} - '
                f'{payment_type.insurance}/{payment_type.service_type.code}'
            ))
            for payment_type in payment_types
        ]


class InsuranceMultiSelectFilter(MultiSelectListFilter):
    title = 'insurance'
    parameter_name = 'insurance_multi'
    field_path = 'payment_type__insurance'

    def lookups(self, request, model_admin):
        return PaymentType._meta.get_field('insurance').choices


class ServiceTypeCodeMultiSelectFilter(MultiSelectListFilter):
    title = 'service type code'
    parameter_name = 'service_type_code_multi'
    field_path = 'payment_type__service_type__code'
    extra_remove_parameters = ('payment_type__service_type__code__exact',)

    def lookups(self, request, model_admin):
        return (
            ServiceType.objects
            .filter(payment_types__employee_records__isnull=False)
            .distinct()
            .order_by('code')
            .values_list('code', 'code')
        )


class LocationMultiSelectFilter(MultiSelectListFilter):
    title = 'location'
    parameter_name = 'location_multi'
    field_path = 'location'

    def lookups(self, request, model_admin):
        return (
            EmployeeRecord.objects
            .exclude(location='')
            .order_by('location')
            .values_list('location', 'location')
            .distinct()
        )


class ServiceTypeSpecializationInline(admin.TabularInline):
    model = ServiceTypeSpecialization
    extra = 1


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ('name', 'center', 'type')
    list_filter   = ('center', 'type')
    search_fields = ('name', 'center__name')


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display  = ('number', 'patient_name', 'group', 'created_at')
    list_filter   = ('center', 'group')
    search_fields = ('number', 'patient_name', 'group__center__name',)


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


# @admin.register(PaymentType)
# class PaymentTypeAdmin(admin.ModelAdmin):
#     list_display    = (
#         'file', 'service_type', 'insurance',
#         'num_of_session', 'sessions_used', 'sessions_remaining'
#     )
#     list_filter     = ('file__group__center', 'file__group', 'service_type__code', 'insurance')
#     search_fields   = ('file__number',)
#     ordering        = ('-created_at',)

@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    autocomplete_fields = ('file',)  # <— type a file number to search
    list_display = (
        'file', 'service_type', 'insurance',
        'num_of_session', 'sessions_used', 'sessions_remaining'
    )
    list_filter = ('file__group__center', 'file__group', 'service_type__code', 'insurance')
    search_fields = ('file__number',)
    ordering = ('-created_at',)

@admin.register(PaymentTypeCanceled)
class PaymentTypeCanceledAdmin(admin.ModelAdmin):
    """View-only list for canceled PaymentType rows."""
    list_display = ('updated_at', 'file_number', 'payment_type', 'cancel_reason')
    ordering = ('-updated_at',)
    search_fields = ('file__number', 'service_type__code', 'service_type__name', 'cancel_reason')
    list_per_page = 50

    # â†“ Filter to only canceled rows. Adjust the predicate to your model.
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If you have a status field:
        if 'status' in [f.name for f in qs.model._meta.get_fields()]:
            return qs.filter(status='canceled')
        # Or if you have a boolean flag:
        if 'is_canceled' in [f.name for f in qs.model._meta.get_fields()]:
            return qs.filter(is_canceled=True)
        # Fallback: no extra filtering (remove if not needed)
        return qs.none()

    # ---- Columns ----
    def file_number(self, obj):
        return getattr(obj.file, 'number', '')
    file_number.short_description = "File Number"
    file_number.admin_order_field = 'file__number'

    def payment_type(self, obj):
        # Pick what represents "payment type" in your model
        # Try code then name on related service_type; adapt if you have a different field.
        if hasattr(obj, 'service_type') and obj.service_type:
            return getattr(obj.service_type, 'code', None) or getattr(obj.service_type, 'name', '')
        return ''
    payment_type.short_description = "Payment Type"
    payment_type.admin_order_field = 'service_type__code'

@admin.register(EmployeeRecord)
class EmployeeRecordAdmin(admin.ModelAdmin):
    list_display = (
        'payment_type', 'location', 'is_session',
        'duration_minutes', 'date', 'created_by'
    )

    list_filter = (
        ('date', DateRangeFilter),
        PaymentTypeMultiSelectFilter,
        InsuranceMultiSelectFilter,
        ServiceTypeCodeMultiSelectFilter,
        LocationMultiSelectFilter,
        'is_session',
        'created_by',
    )

    search_fields = (
        'payment_type__file__number',
        'location',
        'created_by__username',
    )

    ordering = ('-date',)

    def lookup_allowed(self, lookup, value, request=None):
        allowed_lookups = {
            'payment_type',
            'payment_type__exact',
            'payment_type__id__exact',
            'payment_type__service_type__code',
            'payment_type__service_type__code__exact',
            'payment_type__insurance',
            'payment_type__insurance__exact',
            'payment_type__file',
            'payment_type__file__exact',
            'payment_type__file__id__exact',
            'location',
            'location__exact',
        }
        if lookup in allowed_lookups:
            return True
        return super().lookup_allowed(lookup, value, request)


class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    filter_horizontal = ('specializations',)

class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeProfileInline,)

    def get_inline_instances(self, request, obj=None):
        """
        Only show the profile inline when editing an existing user,
        not when creating a new one â€” avoids the duplicate-profile error.
        """
        if obj is None:  # adding a new user
            return []
        return super().get_inline_instances(request, obj)

    # keep your existing list_display etc.
    list_display = BaseUserAdmin.list_display + ('get_specializations',)
    def get_specializations(self, obj):
        return ", ".join(s.name for s in obj.employee_profile.specializations.all())
    get_specializations.short_description = "Specializations"

# Unregister old User admin, register new one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Keep a reference to the original get_urls
_old_get_urls = admin.site.get_urls

@login_required(login_url='/admin/login/')
def download_sqlite(request):
    """
    Streams the SQLite DB fileâ€”but only for logged-in users.
    """
    # If you also want to restrict to superusers, uncomment:
    if not request.user.is_superuser:
        return HttpResponseForbidden("Does Not Exists")
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    return FileResponse(
        open(db_path, 'rb'),
        as_attachment=True,
        filename='db.sqlite3'
    )

def get_urls():
    custom_urls = [
        path(
            'download-db/',
            download_sqlite,
            name='download-db'
        ),
    ]
    return custom_urls + _old_get_urls()

# Monkey-patch the admin site
admin.site.get_urls = get_urls
