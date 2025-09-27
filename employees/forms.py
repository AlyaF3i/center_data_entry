from django import forms

from .models import PaymentType, EmployeeRecord


class EmployeeForm(forms.ModelForm):
    payment_type = forms.ModelChoiceField(
        queryset=PaymentType.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Payment (File • Ins./Service • Remaining)",
    )

    def __init__(self, *args, center=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = PaymentType.objects.filter(is_canceled=False).select_related('file', 'service_type')
        if center is not None:
            qs = qs.filter(file__group__center=center)
        if user is not None and hasattr(user, 'employee_profile'):
            spec_ids = list(user.employee_profile.specializations.values_list('id', flat=True))
            if spec_ids:
                qs = qs.filter(service_type__specializations__in=spec_ids).distinct()
        self.fields['payment_type'].queryset = qs.order_by('file__patient_name', 'service_type__code')

    class Meta:
        model = EmployeeRecord
        fields = [
            'payment_type',
            'location',
            'is_session',
            'duration_minutes',
            'remarks',
        ]
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'is_session': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional remarks'}),
        }
