from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
from django.utils import timezone
from .models import MaintenanceTeam, MaintenanceRequest, MaintenanceHistory
from equipment.models import Equipment
from accounts.models import User


@login_required
def team_list(request):
    if request.method == 'GET':
        teams = MaintenanceTeam.objects.all()
        data = [{
            'id': team.id,
            'name': team.name,
            'leader': team.leader.id if team.leader else None,
            'member_count': team.members.count()
        } for team in teams]
        return JsonResponse({'teams': data})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        team = MaintenanceTeam.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            leader_id=data.get('leader')
        )
        if data.get('members'):
            team.members.set(data['members'])
        return JsonResponse({
            'id': team.id,
            'name': team.name
        }, status=201)


@login_required
def team_detail(request, pk):
    team = get_object_or_404(MaintenanceTeam, pk=pk)
    
    if request.method == 'GET':
        data = {
            'id': team.id,
            'name': team.name,
            'description': team.description,
            'leader': team.leader.id if team.leader else None,
            'leader_details': {
                'id': team.leader.id,
                'first_name': team.leader.first_name,
                'last_name': team.leader.last_name,
                'email': team.leader.email
            } if team.leader else None,
            'members': list(team.members.values_list('id', flat=True)),
            'members_details': [{
                'id': member.id,
                'first_name': member.first_name,
                'last_name': member.last_name,
                'email': member.email,
                'user_type': member.user_type
            } for member in team.members.all()],
            'created_at': team.created_at,
            'updated_at': team.updated_at
        }
        return JsonResponse(data)
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        team.name = data.get('name', team.name)
        team.description = data.get('description', team.description)
        if data.get('leader'):
            team.leader_id = data['leader']
        team.save()
        if data.get('members'):
            team.members.set(data['members'])
        return JsonResponse({'message': 'Team updated successfully'})
    
    elif request.method == 'DELETE':
        team.delete()
        return JsonResponse({'message': 'Team deleted successfully'})


@login_required
def team_add_member(request, pk):
    team = get_object_or_404(MaintenanceTeam, pk=pk)
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            team.members.add(user)
            return JsonResponse({'message': 'Member added successfully'})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)


@login_required
def team_remove_member(request, pk):
    team = get_object_or_404(MaintenanceTeam, pk=pk)
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            team.members.remove(user)
            return JsonResponse({'message': 'Member removed successfully'})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)


@login_required
def request_list(request):
    if request.method == 'GET':
        status_filter = request.GET.get('status')
        priority_filter = request.GET.get('priority')
        my_requests = request.GET.get('my_requests')
        
        requests = MaintenanceRequest.objects.all()
        
        if status_filter:
            requests = requests.filter(status=status_filter)
        if priority_filter:
            requests = requests.filter(priority=priority_filter)
        if my_requests:
            requests = requests.filter(requested_by=request.user)
        
        data = [{
            'id': req.id,
            'title': req.title,
            'status': req.status,
            'priority': req.priority,
            'equipment_name': req.equipment.name,
            'equipment_serial': req.equipment.serial_number,
            'requested_by_name': req.requested_by.first_name if req.requested_by else '',
            'team_name': req.assigned_team.name if req.assigned_team else '',
            'scheduled_date': req.scheduled_date,
            'created_at': req.created_at
        } for req in requests]
        return JsonResponse({'requests': data})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        maintenance_request = MaintenanceRequest.objects.create(
            title=data['title'],
            description=data['description'],
            equipment_id=data['equipment'],
            requested_by=request.user,
            priority=data.get('priority', 'medium'),
            scheduled_date=data.get('scheduled_date'),
            status='pending'
        )
        if data.get('assigned_team'):
            maintenance_request.assigned_team_id = data['assigned_team']
            maintenance_request.status = 'in_progress'
            maintenance_request.save()
        return JsonResponse({
            'id': maintenance_request.id,
            'title': maintenance_request.title,
            'status': maintenance_request.status
        }, status=201)


@login_required
def request_detail(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    
    if request.method == 'GET':
        data = {
            'id': maintenance_request.id,
            'title': maintenance_request.title,
            'description': maintenance_request.description,
            'equipment': maintenance_request.equipment.id,
            'equipment_details': {
                'id': maintenance_request.equipment.id,
                'name': maintenance_request.equipment.name,
                'serial_number': maintenance_request.equipment.serial_number,
                'status': maintenance_request.equipment.status
            },
            'requested_by': maintenance_request.requested_by.id if maintenance_request.requested_by else None,
            'requested_by_details': {
                'id': maintenance_request.requested_by.id,
                'first_name': maintenance_request.requested_by.first_name,
                'email': maintenance_request.requested_by.email
            } if maintenance_request.requested_by else None,
            'assigned_team': maintenance_request.assigned_team.id if maintenance_request.assigned_team else None,
            'assigned_team_details': {
                'id': maintenance_request.assigned_team.id,
                'name': maintenance_request.assigned_team.name
            } if maintenance_request.assigned_team else None,
            'status': maintenance_request.status,
            'priority': maintenance_request.priority,
            'scheduled_date': maintenance_request.scheduled_date,
            'completed_date': maintenance_request.completed_date,
            'created_at': maintenance_request.created_at,
            'updated_at': maintenance_request.updated_at
        }
        return JsonResponse(data)
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        maintenance_request.title = data.get('title', maintenance_request.title)
        maintenance_request.description = data.get('description', maintenance_request.description)
        maintenance_request.priority = data.get('priority', maintenance_request.priority)
        maintenance_request.scheduled_date = data.get('scheduled_date', maintenance_request.scheduled_date)
        if data.get('assigned_team'):
            maintenance_request.assigned_team_id = data['assigned_team']
        if data.get('status'):
            maintenance_request.status = data['status']
        maintenance_request.save()
        return JsonResponse({'message': 'Request updated successfully'})
    
    elif request.method == 'DELETE':
        maintenance_request.delete()
        return JsonResponse({'message': 'Request deleted successfully'})


@login_required
def request_assign_team(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    if request.method == 'POST':
        data = json.loads(request.body)
        team_id = data.get('team_id')
        try:
            team = MaintenanceTeam.objects.get(id=team_id)
            maintenance_request.assigned_team = team
            maintenance_request.status = 'in_progress'
            maintenance_request.save()
            return JsonResponse({'message': 'Team assigned successfully'})
        except MaintenanceTeam.DoesNotExist:
            return JsonResponse({'error': 'Team not found'}, status=404)


@login_required
def request_complete(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    if request.method == 'POST':
        data = json.loads(request.body)
        maintenance_request.status = 'completed'
        maintenance_request.completed_date = timezone.now().date()
        maintenance_request.save()
        
        MaintenanceHistory.objects.create(
            maintenance_request=maintenance_request,
            performed_by=request.user,
            notes=data.get('notes', ''),
            cost=data.get('cost'),
            parts_used=data.get('parts_used', '')
        )
        
        return JsonResponse({'message': 'Maintenance request completed'})


@login_required
def history_list(request):
    if request.method == 'GET':
        request_id = request.GET.get('request_id')
        history = MaintenanceHistory.objects.all()
        
        if request_id:
            history = history.filter(maintenance_request_id=request_id)
        
        data = [{
            'id': h.id,
            'maintenance_request': h.maintenance_request.id,
            'performed_by_name': h.performed_by.first_name if h.performed_by else '',
            'notes': h.notes,
            'cost': h.cost,
            'created_at': h.created_at
        } for h in history]
        return JsonResponse({'history': data})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        history = MaintenanceHistory.objects.create(
            maintenance_request_id=data['maintenance_request'],
            performed_by_id=data.get('performed_by'),
            notes=data['notes'],
            cost=data.get('cost'),
            parts_used=data.get('parts_used', '')
        )
        return JsonResponse({
            'id': history.id,
            'maintenance_request': history.maintenance_request.id
        }, status=201)


@login_required
def history_detail(request, pk):
    history = get_object_or_404(MaintenanceHistory, pk=pk)
    
    if request.method == 'GET':
        data = {
            'id': history.id,
            'maintenance_request': history.maintenance_request.id,
            'maintenance_request_title': history.maintenance_request.title,
            'performed_by': history.performed_by.id if history.performed_by else None,
            'performed_by_details': {
                'id': history.performed_by.id,
                'first_name': history.performed_by.first_name,
                'email': history.performed_by.email
            } if history.performed_by else None,
            'notes': history.notes,
            'cost': history.cost,
            'parts_used': history.parts_used,
            'created_at': history.created_at
        }
        return JsonResponse(data)
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        history.notes = data.get('notes', history.notes)
        history.cost = data.get('cost', history.cost)
        history.parts_used = data.get('parts_used', history.parts_used)
        history.save()
        return JsonResponse({'message': 'History updated successfully'})
    
    elif request.method == 'DELETE':
        history.delete()
        return JsonResponse({'message': 'History deleted successfully'})


@login_required
def dashboard(request):
    if request.method == 'GET':
        # Equipment statistics
        total_equipment = Equipment.objects.count()
        active_equipment = Equipment.objects.filter(status='active').count()
        maintenance_equipment = Equipment.objects.filter(status='maintenance').count()
        
        # Maintenance request statistics
        total_requests = MaintenanceRequest.objects.count()
        pending_requests = MaintenanceRequest.objects.filter(status='pending').count()
        in_progress_requests = MaintenanceRequest.objects.filter(status='in_progress').count()
        completed_requests = MaintenanceRequest.objects.filter(status='completed').count()
        
        # Team & Worker statistics
        total_teams = MaintenanceTeam.objects.count()
        active_workers = User.objects.filter(is_active=True).count()
        
        # Recent requests
        recent_requests = MaintenanceRequest.objects.order_by('-created_at')[:5]
        recent_data = [{
            'id': req.id,
            'title': req.title,
            'status': req.status,
            'priority': req.priority,
            'equipment_name': req.equipment.name,
            'equipment_serial': req.equipment.serial_number,
            'requested_by_name': req.requested_by.first_name if req.requested_by else (req.requested_by.email if req.requested_by else ''),
            'team_name': req.assigned_team.name if req.assigned_team else '',
            'scheduled_date': req.scheduled_date,
            'created_at': req.created_at
        } for req in recent_requests]
        
        # Urgent requests
        urgent_requests = MaintenanceRequest.objects.filter(
            priority='urgent', 
            status__in=['pending', 'in_progress']
        )
        urgent_data = [{
            'id': req.id,
            'title': req.title,
            'status': req.status,
            'priority': req.priority,
            'equipment_name': req.equipment.name,
            'equipment_serial': req.equipment.serial_number,
            'requested_by_name': req.requested_by.first_name if req.requested_by else (req.requested_by.email if req.requested_by else ''),
            'team_name': req.assigned_team.name if req.assigned_team else '',
            'scheduled_date': req.scheduled_date,
            'created_at': req.created_at
        } for req in urgent_requests]

        if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
            return JsonResponse({
                'equipment_stats': {
                    'total': total_equipment,
                    'active': active_equipment,
                    'under_maintenance': maintenance_equipment,
                },
                'request_stats': {
                    'total': total_requests,
                    'pending': pending_requests,
                    'in_progress': in_progress_requests,
                    'completed': completed_requests,
                },
                'team_stats': {
                    'total': total_teams,
                },
                'recent_requests': recent_data,
                'urgent_requests': urgent_data,
            })
        
        context = {
            'total_equipment': total_equipment,
            'active_equipment': active_equipment,
            'maintenance_equipment': maintenance_equipment,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'in_progress_requests': in_progress_requests,
            'completed_requests': completed_requests,
            'total_teams': total_teams,
            'active_workers': active_workers,
            'recent_requests': recent_requests,
            'urgent_requests': urgent_requests,
        }
        return render(request, 'dashboard.html', context)


@login_required
def tickets_view(request):
    requests = MaintenanceRequest.objects.all().order_by('-created_at')
    return render(request, 'tickets.html', {'requests': requests})


@login_required
def create_ticket_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        equipment_id = request.POST.get('equipment')
        priority = request.POST.get('priority', 'medium')
        
        if title and description and equipment_id:
            MaintenanceRequest.objects.create(
                title=title,
                description=description,
                equipment_id=equipment_id,
                requested_by=request.user,
                priority=priority
            )
            return redirect('tickets')
            
    equipments = Equipment.objects.all()
    return render(request, 'create-ticket.html', {'equipments': equipments})


@login_required
def workers_view(request):
    workers = User.objects.all()
    teams = MaintenanceTeam.objects.all()
    return render(request, 'workers.html', {'workers': workers, 'teams': teams})


@login_required
def analytics_view(request):
    return render(request, 'analytics.html')


@login_required
def settings_view(request):
    return render(request, 'settings.html')

