from django import forms
from .models import PaymentType, EmployeeRecord

class EmployeeForm(forms.ModelForm):
    payment_type = forms.ModelChoiceField(
        queryset=PaymentType.objects.select_related('file'),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Payment (File • Ins./Service • Remaining)"
    )

    class Meta:
        model  = EmployeeRecord
        fields = [
            'payment_type',
            'location',
            'is_session',
            # 'patient_name',
            'duration_minutes',
            'remarks',
        ]
        widgets = {
            'location':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'is_session':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # 'patient_name':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter patient name'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
            'remarks':          forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional remarks'}),
        }
