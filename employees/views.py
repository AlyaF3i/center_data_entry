from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .forms import EmployeeForm
from .models import Center, EmployeeRecord, File, Group, PaymentType


def _get_active_center(request):
    center_id = request.session.get('active_center_id')
    if not center_id:
        return None
    try:
        return Center.objects.get(pk=center_id, is_active=True)
    except Center.DoesNotExist:
        request.session.pop('active_center_id', None)
        request.session.pop('active_center_name', None)
        return None


def _redirect_to_center_picker(request):
    next_url = request.get_full_path()
    query = urlencode({'next': next_url}) if next_url else ''
    url = reverse('select_center')
    if query:
        url = f"{url}?{query}"
    return redirect(url)


@login_required
def select_center(request):
    centers = Center.objects.filter(is_active=True).order_by('name')
    current_center_id = request.session.get('active_center_id')
    next_url = request.GET.get('next') or reverse('record_list')
    error = None

    if request.method == 'POST':
        center_id = request.POST.get('center_id')
        redirect_target = request.POST.get('next') or reverse('record_list')
        try:
            center = centers.get(pk=center_id)
        except (Center.DoesNotExist, ValueError, TypeError):
            error = 'Please choose a valid center.'
        else:
            request.session['active_center_id'] = center.id
            request.session['active_center_name'] = center.name
            request.session.modified = True
            return redirect(redirect_target)

    return render(
        request,
        'employees/select_center.html',
        {
            'centers': centers,
            'current_center_id': current_center_id,
            'next': next_url,
            'error': error,
        },
    )


@login_required
def create_record(request):
    center = _get_active_center(request)
    if center is None:
        return _redirect_to_center_picker(request)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, center=center, user=request.user)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.created_by = request.user
            rec.save()
            return redirect('record_list')
    else:
        form = EmployeeForm(center=center, user=request.user)

    groups = (
        Group.objects.filter(Q(center=center) | Q(files__center=center))
        .distinct()
        .order_by('name')
    )
    return render(
        request,
        'employees/employee_form.html',
        {
            'form': form,
            'groups': groups,
            'active_center': center,
        },
    )


@login_required
def edit_record(request, pk):
    center = _get_active_center(request)
    if center is None:
        return _redirect_to_center_picker(request)

    record = get_object_or_404(
        EmployeeRecord,
        pk=pk,
        created_by=request.user,
        payment_type__file__group__center=center,
    )

    if datetime.now() - record.date > timedelta(hours=1):
        return HttpResponseForbidden("Editing time window has expired.")

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=record, center=center, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('record_list')
    else:
        form = EmployeeForm(instance=record, center=center, user=request.user)
    return render(request, 'employees/employee_edit_form.html', {'form': form, 'active_center': center})


@login_required
def list_records(request):
    center = _get_active_center(request)
    if center is None:
        return _redirect_to_center_picker(request)

    if not request.user.is_superuser:
        qs = EmployeeRecord.objects.filter(
            created_by=request.user,
            payment_type__file__group__center=center,
        )
    else:
        qs = EmployeeRecord.objects.filter(payment_type__file__group__center=center)

    file_filter = request.GET.get('file')
    place_filter = request.GET.get('place')
    insurance_filter = request.GET.get('insurance')

    if file_filter:
        qs = qs.filter(payment_type__file__number=file_filter)
    if place_filter:
        qs = qs.filter(location__icontains=place_filter)
    if insurance_filter:
        qs = qs.filter(payment_type__insurance=insurance_filter)

    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
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

    cutoff = datetime.now() - timedelta(hours=1)
    editable_pks = list(qs.filter(date__gte=cutoff).values_list('pk', flat=True))

    records = qs.order_by('-date')
    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_pages = paginator.num_pages or 1
    current_page = page_obj.number
    window = 2
    start_page = max(current_page - window, 1)
    end_page = min(current_page + window, total_pages)
    page_numbers = []
    if start_page > 1:
        page_numbers.append(1)
        if start_page > 2:
            page_numbers.append(None)
    page_numbers.extend(range(start_page, end_page + 1))
    if end_page < total_pages:
        if end_page < total_pages - 1:
            page_numbers.append(None)
        page_numbers.append(total_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    query_string = query_params.urlencode()

    return render(
        request,
        'employees/employee_list.html',
        {
            'records': page_obj.object_list,
            'page_obj': page_obj,
            'paginator': paginator,
            'total_pages': total_pages,
            'page_numbers': page_numbers,
            'query_string': query_string,
            'file': file_filter or '',
            'place': place_filter or '',
            'insurance': insurance_filter or '',
            'start': start_str or '',
            'end': end_str or '',
            'editable_pks': editable_pks,
            'active_center': center,
        },
    )


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@require_GET
@login_required
def get_payment_types(request):
    center = _get_active_center(request)
    if center is None:
        return JsonResponse({'payment_types': []})

    file_number = request.GET.get('file_number')
    try:
        f = File.objects.get(number=file_number, group__center=center)
    except (File.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'payment_types': []})

    pts = PaymentType.objects.filter(file=f, is_canceled=False)
    if hasattr(request.user, 'employee_profile'):
        spec_names = list(request.user.employee_profile.specializations.values_list('name', flat=True))
        if spec_names:
            pts = pts.filter(service_type__specializations__name__in=spec_names)
    pts = pts.order_by('service_type__code', 'insurance', '-created_at').distinct()

    seen = set()
    data = []
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
    center = _get_active_center(request)
    if center is None:
        return JsonResponse({'results': []})

    group_id = request.GET.get('group_id')
    q = request.GET.get('q', '').strip()

    qs = File.objects.filter(group__center=center)
    if group_id:
        qs = qs.filter(group_id=group_id)

    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(patient_name__icontains=q))

    data = []
    for f in qs.order_by('number')[:50]:
        data.append({
            'id': f.number,
            'text': f"#{f.number} – {f.patient_name}",
        })

    return JsonResponse({'results': data})
