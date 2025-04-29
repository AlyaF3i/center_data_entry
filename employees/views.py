from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from datetime import timedelta
from .forms import EmployeeForm
from django.contrib.auth import logout
from django.views.decorators.http import require_GET
from .models import File, PaymentType, EmployeeRecord
from datetime import datetime, timedelta

@login_required
def create_record(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.created_by = request.user
            record.save()
            return redirect('record_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form})

@login_required
def edit_record(request, pk):
    record = get_object_or_404(EmployeeRecord, pk=pk, created_by=request.user)
    # Only allow edits within 1 hour
    if timezone.now() - record.date > timedelta(hours=1):
        return HttpResponseForbidden("Editing time window has expired.")
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('record_list')
    else:
        form = EmployeeForm(instance=record)
    return render(request, 'employees/employee_form.html', {'form': form})

@login_required
def list_records(request):
    qs = EmployeeRecord.objects.filter(created_by=request.user)

    # Existing filters
    file_filter      = request.GET.get('file')
    place_filter     = request.GET.get('place')
    insurance_filter = request.GET.get('insurance')

    if file_filter:
        qs = qs.filter(payment_type__file__number=file_filter)
    if place_filter:
        qs = qs.filter(service_place__icontains=place_filter)
    if insurance_filter:
        qs = qs.filter(payment_type__insurance=insurance_filter)

    # New start/end date filters (expects YYYY-MM-DD)
    start_str = request.GET.get('start')
    end_str   = request.GET.get('end')
    if start_str:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            qs = qs.filter(date__date__gte=start_date)
        except ValueError:
            pass
    if end_str:
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            qs = qs.filter(date__date__lte=end_date)
        except ValueError:
            pass

    # Determine editable records (within 1 hour)
    cutoff = timezone.now() - timedelta(hours=1)
    editable_pks = list(qs.filter(date__gte=cutoff).values_list('pk', flat=True))

    records = qs.order_by('-date')
    return render(request, 'employees/employee_list.html', {
        'records':    records,
        'file':       file_filter or '',
        'place':      place_filter or '',
        'insurance':  insurance_filter or '',
        'start':      start_str or '',
        'end':        end_str or '',
        'editable_pks': editable_pks,
    })
    
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@require_GET
@login_required
def get_payment_types(request):
    """
    Given ?file_number=123, return a single entry for each
    unique (service_type, insurance) under that File, choosing
    the most recent PaymentType as the label.
    """
    file_number = request.GET.get('file_number')
    data = []
    
    try:
        f = File.objects.get(number=file_number)
    except File.DoesNotExist:
        return JsonResponse({'payment_types': []})

    # Order so that newest for each pair comes first
    pts = (
        PaymentType.objects
        .filter(file=f)
        .order_by('service_type', 'insurance', '-created_at')
    )

    seen = set()
    for pt in pts:
        key = (pt.service_type, pt.insurance)
        if key in seen:
            continue
        seen.add(key)
        data.append({
            'id':    pt.id,
            'label': str(pt),
        })

    return JsonResponse({'payment_types': data})