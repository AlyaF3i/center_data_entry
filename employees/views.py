from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from datetime import timedelta
from .forms import EmployeeForm
from django.contrib.auth import logout
from django.views.decorators.http import require_GET
from .models import File, PaymentType, EmployeeRecord, Group
from datetime import datetime, timedelta
from django.db.models import Q

@login_required
def create_record(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.created_by = request.user
            rec.save()
            return redirect('record_list')
    else:
        form = EmployeeForm()

    # Pass all groups for the “By Patient” selector
    groups = Group.objects.all()
    return render(request, 'employees/employee_form.html', {
        'form':   form,
        'groups': groups,
    })

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
    if not request.user.is_super:
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
    file_number = request.GET.get('file_number')
    try:
        f = File.objects.get(number=file_number)
    except File.DoesNotExist:
        return JsonResponse({'payment_types': []})

    pts = PaymentType.objects.filter(file=f)
    # gather user specs
    specs = request.user.employee_profile.specializations.values_list('name', flat=True)

    pts = pts.filter(service_type__specializations__name__in=specs)

    # dedupe and return
    pts = pts.order_by('service_type__code', 'insurance', '-created_at')
    seen, data = set(), []
    for pt in pts:
        key = (pt.service_type.code, pt.insurance)
        if key in seen:
            continue
        seen.add(key)
        data.append({'id': pt.id, 'label': str(pt)})
    return JsonResponse({'payment_types': data})

@require_GET
@login_required
def get_files(request):
    """
    AJAX endpoint for Select2:
    – Expects ?group_id=<id>&q=<search_term>
    – Returns one entry per File.number in that group
    """
    group_id = request.GET.get('group_id')
    q        = request.GET.get('q', '').strip()

    qs = File.objects.filter(group_id=group_id)
    if q:
        qs = qs.filter(
            Q(number__icontains=q) |
            Q(patient_name__icontains=q)
        )

    data = []
    for f in qs.order_by('number')[:50]:
        data.append({
            # Use the File.number as the “id” so it hooks into your loadPaymentTypes(fn)
            'id': f.number,
            'text': f"#{f.number} – {f.patient_name}"
        })

    return JsonResponse({'results': data})