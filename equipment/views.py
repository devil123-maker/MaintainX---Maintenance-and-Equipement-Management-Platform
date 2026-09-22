from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from .models import Equipment


@login_required
def equipment_list(request):
    if request.method == 'GET':
        status_filter = request.GET.get('status')
        if status_filter and status_filter != 'all':
            equipment_qs = Equipment.objects.filter(status=status_filter)
        else:
            equipment_qs = Equipment.objects.all()
        
        equipment_qs = equipment_qs.prefetch_related('maintenance_requests', 'assigned_employee', 'maintenance_team', 'default_technician')

        accept_header = request.headers.get('Accept', '')
        wants_html = 'text/html' in accept_header and request.GET.get('format') != 'json'

        if wants_html:
            return render(request, 'equipment.html', {'equipments': equipment_qs, 'current_status': status_filter or 'all'})

        data = [{
            'id': eq.id,
            'name': eq.name,
            'serial_number': eq.serial_number,
            'status': eq.status,
            'location': eq.location,
            'category': eq.category,
            'department': eq.department,
            'warranty_expiry_date': eq.warranty_expiry_date,
            'assigned_employee': eq.assigned_employee.id if eq.assigned_employee else None,
            'maintenance_team': eq.maintenance_team.id if eq.maintenance_team else None,
            'default_technician': eq.default_technician.id if eq.default_technician else None,
            'total_maintenance_requests': eq.maintenance_count,
            'open_maintenance_requests': eq.open_maintenance_count,
        } for eq in equipment_qs]
        return JsonResponse({'equipment': data})
    
    elif request.method == 'POST':
        if not request.user.can_manage_equipment:
            return JsonResponse({'error': 'Permission denied. Only admins or managers can create equipment.'}, status=403)
        data = json.loads(request.body)
        equipment = Equipment.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            serial_number=data['serial_number'],
            model=data.get('model', ''),
            manufacturer=data.get('manufacturer', ''),
            category=data.get('category', ''),
            department=data.get('department', ''),
            purchase_date=data.get('purchase_date'),
            warranty_expiry_date=data.get('warranty_expiry_date'),
            location=data.get('location', ''),
            status=data.get('status', 'active'),
            created_by=request.user,
            assigned_employee_id=data.get('assigned_employee'),
            maintenance_team_id=data.get('maintenance_team'),
            default_technician_id=data.get('default_technician'),
        )
        return JsonResponse({
            'id': equipment.id,
            'name': equipment.name,
            'serial_number': equipment.serial_number,
            'status': equipment.status
        }, status=201)


@login_required
def equipment_detail(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    
    if request.method == 'GET':
        accept_header = request.headers.get('Accept', '')
        wants_html = 'text/html' in accept_header and request.GET.get('format') != 'json'

        if wants_html:
            from django.shortcuts import redirect
            return redirect('equipment_maintenance', pk=pk)

        latest_req = equipment.latest_maintenance_request
        data = {
            'id': equipment.id,
            'name': equipment.name,
            'description': equipment.description,
            'serial_number': equipment.serial_number,
            'model': equipment.model,
            'manufacturer': equipment.manufacturer,
            'category': equipment.category,
            'department': equipment.department,
            'purchase_date': equipment.purchase_date,
            'warranty_expiry_date': equipment.warranty_expiry_date,
            'location': equipment.location,
            'status': equipment.status,
            'created_at': equipment.created_at,
            'updated_at': equipment.updated_at,
            'created_by': equipment.created_by.id if equipment.created_by else None,
            'created_by_name': equipment.created_by.first_name if equipment.created_by else '',
            'created_by_email': equipment.created_by.email if equipment.created_by else '',
            'assigned_employee': equipment.assigned_employee.id if equipment.assigned_employee else None,
            'maintenance_team': equipment.maintenance_team.id if equipment.maintenance_team else None,
            'maintenance_team_name': equipment.maintenance_team.name if equipment.maintenance_team else '',
            'default_technician': equipment.default_technician.id if equipment.default_technician else None,
            'default_technician_name': equipment.default_technician.first_name if equipment.default_technician else '',
            'total_maintenance_requests': equipment.maintenance_count,
            'open_maintenance_requests': equipment.open_maintenance_count,
            'latest_maintenance_request': {
                'id': latest_req.id,
                'title': latest_req.title,
                'status': latest_req.status,
                'request_type': latest_req.request_type,
                'created_at': latest_req.created_at.isoformat()
            } if latest_req else None
        }
        return JsonResponse(data)
    
    elif request.method == 'PUT':
        if not request.user.can_manage_equipment:
            return JsonResponse({'error': 'Permission denied. Only admins or managers can update equipment.'}, status=403)
        data = json.loads(request.body)
        equipment.name = data.get('name', equipment.name)
        equipment.description = data.get('description', equipment.description)
        equipment.serial_number = data.get('serial_number', equipment.serial_number)
        equipment.model = data.get('model', equipment.model)
        equipment.manufacturer = data.get('manufacturer', equipment.manufacturer)
        equipment.category = data.get('category', equipment.category)
        equipment.department = data.get('department', equipment.department)
        equipment.purchase_date = data.get('purchase_date', equipment.purchase_date)
        equipment.warranty_expiry_date = data.get('warranty_expiry_date', equipment.warranty_expiry_date)
        equipment.location = data.get('location', equipment.location)
        equipment.status = data.get('status', equipment.status)
        if 'assigned_employee' in data:
            equipment.assigned_employee_id = data['assigned_employee']
        if 'maintenance_team' in data:
            equipment.maintenance_team_id = data['maintenance_team']
        if 'default_technician' in data:
            equipment.default_technician_id = data['default_technician']
        equipment.save()
        return JsonResponse({'message': 'Equipment updated successfully'})
    
    elif request.method == 'DELETE':
        if not request.user.can_manage_equipment:
            return JsonResponse({'error': 'Permission denied. Only admins or managers can delete equipment.'}, status=403)
        equipment.delete()
        return JsonResponse({'message': 'Equipment deleted successfully'})


@login_required
def equipment_maintenance(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    requests_qs = equipment.maintenance_requests.select_related('assigned_team', 'assigned_technician', 'equipment').order_by('-created_at')
    
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        data = {
            'equipment_id': equipment.id,
            'equipment_name': equipment.name,
            'equipment_serial': equipment.serial_number,
            'status': equipment.status,
            'total_requests': equipment.maintenance_count,
            'open_requests': equipment.open_maintenance_count,
            'requests': [{
                'id': req.id,
                'title': req.title,
                'request_type': req.request_type,
                'status': req.status,
                'priority': req.priority,
                'scheduled_date': req.scheduled_date.isoformat() if req.scheduled_date else None,
                'duration_display': req.duration_display,
                'is_overdue': req.is_overdue
            } for req in requests_qs]
        }
        return JsonResponse(data)

    context = {
        'equipment': equipment,
        'maintenance_requests': requests_qs,
        'total_count': equipment.maintenance_count,
        'open_count': equipment.open_maintenance_count,
        'latest_request': equipment.latest_maintenance_request
    }
    return render(request, 'equipment_maintenance.html', context)
