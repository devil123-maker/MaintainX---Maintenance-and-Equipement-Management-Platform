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
        if status_filter:
            equipment = Equipment.objects.filter(status=status_filter)
        else:
            equipment = Equipment.objects.all()
        
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
        } for eq in equipment]
        return JsonResponse({'equipment': data})
    
    elif request.method == 'POST':
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
        }
        return JsonResponse(data)
    
    elif request.method == 'PUT':
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
        equipment.delete()
        return JsonResponse({'message': 'Equipment deleted successfully'})
