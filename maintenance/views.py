from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
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
        if not request.user.is_admin_user:
            return JsonResponse({'error': 'Permission denied. Only admins or managers can create teams.'}, status=403)
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
        if not (request.user.is_admin_user or team.leader == request.user):
            return JsonResponse({'error': 'Permission denied. Only team leaders or admins can update this team.'}, status=403)
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
        if not request.user.is_admin_user:
            return JsonResponse({'error': 'Permission denied. Only admins can delete teams.'}, status=403)
        team.delete()
        return JsonResponse({'message': 'Team deleted successfully'})


@login_required
def team_add_member(request, pk):
    team = get_object_or_404(MaintenanceTeam, pk=pk)
    if not (request.user.is_admin_user or team.leader == request.user):
        return JsonResponse({'error': 'Permission denied.'}, status=403)
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
    if not (request.user.is_admin_user or team.leader == request.user):
        return JsonResponse({'error': 'Permission denied.'}, status=403)
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
        type_filter = request.GET.get('request_type')
        my_requests = request.GET.get('my_requests')
        
        requests = MaintenanceRequest.objects.all()
        
        if status_filter:
            requests = requests.filter(status=status_filter)
        if priority_filter:
            requests = requests.filter(priority=priority_filter)
        if type_filter:
            requests = requests.filter(request_type=type_filter)
        if my_requests:
            requests = requests.filter(requested_by=request.user)
        
        data = [{
            'id': req.id,
            'title': req.title,
            'status': req.status,
            'priority': req.priority,
            'request_type': req.request_type,
            'equipment_name': req.equipment.name,
            'equipment_serial': req.equipment.serial_number,
            'requested_by_name': req.requested_by.first_name if req.requested_by else '',
            'team_name': req.assigned_team.name if req.assigned_team else '',
            'assigned_technician': req.assigned_technician.id if req.assigned_technician else None,
            'assigned_technician_name': req.assigned_technician.first_name if req.assigned_technician else '',
            'duration_hours': float(req.duration_hours) if req.duration_hours is not None else None,
            'scheduled_date': req.scheduled_date,
            'created_at': req.created_at
        } for req in requests]
        return JsonResponse({'requests': data})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        try:
            maintenance_request = MaintenanceRequest.objects.create(
                title=data['title'],
                description=data['description'],
                equipment_id=data['equipment'],
                requested_by=request.user,
                priority=data.get('priority', 'medium'),
                request_type=data.get('request_type', 'corrective'),
                scheduled_date=data.get('scheduled_date'),
                duration_hours=data.get('duration_hours'),
                duration_value=data.get('duration_value'),
                duration_unit=data.get('duration_unit', 'minutes'),
                assigned_technician_id=data.get('assigned_technician'),
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
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict if hasattr(e, 'message_dict') else str(e)}, status=400)


@login_required
def request_detail(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    
    if request.method == 'GET':
        data = {
            'id': maintenance_request.id,
            'title': maintenance_request.title,
            'description': maintenance_request.description,
            'request_type': maintenance_request.request_type,
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
            'assigned_technician': maintenance_request.assigned_technician.id if maintenance_request.assigned_technician else None,
            'assigned_technician_details': {
                'id': maintenance_request.assigned_technician.id,
                'first_name': maintenance_request.assigned_technician.first_name,
                'email': maintenance_request.assigned_technician.email
            } if maintenance_request.assigned_technician else None,
            'status': maintenance_request.status,
            'priority': maintenance_request.priority,
            'duration_hours': float(maintenance_request.duration_hours) if maintenance_request.duration_hours is not None else None,
            'duration_value': float(maintenance_request.duration_value) if maintenance_request.duration_value is not None else None,
            'duration_unit': maintenance_request.duration_unit,
            'duration_display': maintenance_request.duration_display,
            'scheduled_date': maintenance_request.scheduled_date,
            'completed_date': maintenance_request.completed_date,
            'created_at': maintenance_request.created_at,
            'updated_at': maintenance_request.updated_at
        }
        return JsonResponse(data)
    
    elif request.method == 'PUT':
        if not request.user.can_edit_request(maintenance_request):
            return JsonResponse({'error': 'Permission denied. You are not authorized to update this request.'}, status=403)
        data = json.loads(request.body)
        try:
            maintenance_request.title = data.get('title', maintenance_request.title)
            maintenance_request.description = data.get('description', maintenance_request.description)
            maintenance_request.priority = data.get('priority', maintenance_request.priority)
            maintenance_request.request_type = data.get('request_type', maintenance_request.request_type)
            maintenance_request.scheduled_date = data.get('scheduled_date', maintenance_request.scheduled_date)
            if 'duration_hours' in data:
                maintenance_request.duration_hours = data['duration_hours']
            if 'duration_value' in data:
                maintenance_request.duration_value = data['duration_value']
            if 'duration_unit' in data:
                maintenance_request.duration_unit = data['duration_unit']
            if 'assigned_team' in data:
                if not request.user.can_assign_requests:
                    return JsonResponse({'error': 'Permission denied. Only admins or team leaders can reassign teams.'}, status=403)
                maintenance_request.assigned_team_id = data['assigned_team']
            if 'assigned_technician' in data:
                maintenance_request.assigned_technician_id = data['assigned_technician']
            if 'status' in data:
                maintenance_request.status = data['status']
            maintenance_request.save()
            return JsonResponse({'message': 'Request updated successfully'})
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict if hasattr(e, 'message_dict') else str(e)}, status=400)
    
    elif request.method == 'DELETE':
        if not request.user.is_admin_user:
            return JsonResponse({'error': 'Permission denied. Only admins can delete requests.'}, status=403)
        maintenance_request.delete()
        return JsonResponse({'message': 'Request deleted successfully'})


@login_required
def request_assign_team(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    if not request.user.can_assign_requests:
        return JsonResponse({'error': 'Permission denied. Only admins or team leaders can assign teams.'}, status=403)
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
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict if hasattr(e, 'message_dict') else str(e)}, status=400)


@login_required
def request_complete(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    if not request.user.can_edit_request(maintenance_request):
        return JsonResponse({'error': 'Permission denied.'}, status=403)
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
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
        except ValidationError as e:
            return JsonResponse({'error': e.message_dict if hasattr(e, 'message_dict') else str(e)}, status=400)


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
        pending_requests = MaintenanceRequest.objects.filter(status__in=['pending', 'new']).count()
        in_progress_requests = MaintenanceRequest.objects.filter(status='in_progress').count()
        completed_requests = MaintenanceRequest.objects.filter(status__in=['completed', 'repaired']).count()
        
        # Team & Worker statistics
        total_teams = MaintenanceTeam.objects.count()
        active_workers = User.objects.filter(is_active=True).count()
        
        # Recent requests
        recent_requests = MaintenanceRequest.objects.select_related(
            'equipment', 'requested_by', 'assigned_team'
        ).order_by('-created_at')[:5]
        recent_data = [{
            'id': req.id,
            'title': req.title,
            'status': req.status,
            'priority': req.priority,
            'request_type': req.request_type,
            'equipment_name': req.equipment.name,
            'equipment_serial': req.equipment.serial_number,
            'requested_by_name': req.requested_by.first_name if req.requested_by else (req.requested_by.email if req.requested_by else ''),
            'team_name': req.assigned_team.name if req.assigned_team else '',
            'scheduled_date': req.scheduled_date,
            'created_at': req.created_at
        } for req in recent_requests]
        
        # Urgent requests
        urgent_requests = MaintenanceRequest.objects.select_related(
            'equipment', 'requested_by', 'assigned_team'
        ).filter(
            priority='urgent', 
            status__in=['pending', 'new', 'in_progress']
        )
        urgent_data = [{
            'id': req.id,
            'title': req.title,
            'status': req.status,
            'priority': req.priority,
            'request_type': req.request_type,
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
    equipment_id = request.GET.get('equipment')
    requests = MaintenanceRequest.objects.select_related(
        'equipment', 'assigned_team', 'assigned_technician', 'requested_by'
    ).order_by('-created_at')
    if equipment_id:
        requests = requests.filter(equipment_id=equipment_id)
    return render(request, 'tickets.html', {'requests': requests, 'selected_equipment_id': equipment_id})


@login_required
def create_ticket_view(request):
    selected_equipment_id = request.GET.get('equipment')
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        equipment_id = request.POST.get('equipment')
        priority = request.POST.get('priority', 'medium')
        request_type = request.POST.get('request_type', 'corrective')
        scheduled_date = request.POST.get('scheduled_date')
        assigned_team_id = request.POST.get('assigned_team')
        assigned_technician_id = request.POST.get('assigned_technician')
        duration_hours = request.POST.get('duration_hours')
        duration_value = request.POST.get('duration_value')
        duration_unit = request.POST.get('duration_unit', 'minutes')
        
        if title and description and equipment_id:
            try:
                MaintenanceRequest.objects.create(
                    title=title,
                    description=description,
                    equipment_id=equipment_id,
                    requested_by=request.user,
                    priority=priority,
                    request_type=request_type,
                    scheduled_date=scheduled_date if scheduled_date else None,
                    assigned_team_id=assigned_team_id if assigned_team_id else None,
                    assigned_technician_id=assigned_technician_id if assigned_technician_id else None,
                    duration_hours=duration_hours if duration_hours else None,
                    duration_value=duration_value if duration_value else None,
                    duration_unit=duration_unit
                )
                return redirect('tickets')
            except ValidationError as e:
                equipments = Equipment.objects.all()
                teams = MaintenanceTeam.objects.all()
                technicians = User.objects.filter(user_type='technician')
                error_msg = e.messages[0] if hasattr(e, 'messages') else str(e)
                return render(request, 'create-ticket.html', {
                    'equipments': equipments,
                    'teams': teams,
                    'technicians': technicians,
                    'error': error_msg,
                    'selected_equipment_id': equipment_id
                })
            
    equipments = Equipment.objects.all()
    teams = MaintenanceTeam.objects.all()
    technicians = User.objects.filter(user_type='technician')
    return render(request, 'create-ticket.html', {
        'equipments': equipments,
        'teams': teams,
        'technicians': technicians,
        'selected_equipment_id': selected_equipment_id
    })


@login_required
def workers_view(request):
    workers = User.objects.all()
    teams = MaintenanceTeam.objects.all()
    return render(request, 'workers.html', {'workers': workers, 'teams': teams})


@login_required
def analytics_view(request):
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        from django.db.models import Count, Avg, Q

        total_requests = MaintenanceRequest.objects.count()
        completed_count = MaintenanceRequest.objects.filter(status__in=['completed', 'repaired']).count()
        open_count = MaintenanceRequest.objects.filter(status__in=['pending', 'new', 'in_progress']).count()
        scrap_count = MaintenanceRequest.objects.filter(status='scrap').count()

        completed_reqs = MaintenanceRequest.objects.filter(status__in=['completed', 'repaired'])
        total_completed = completed_reqs.count()
        if total_completed > 0:
            on_time_count = sum(1 for r in completed_reqs if not r.is_overdue)
            sla_compliance = int(round((on_time_count / total_completed) * 100))
        else:
            sla_compliance = 100

        avg_hours_data = MaintenanceRequest.objects.filter(
            status__in=['completed', 'repaired'],
            duration_hours__isnull=False
        ).aggregate(avg_h=Avg('duration_hours'))
        avg_resolution_hours = round(float(avg_hours_data['avg_h']), 1) if avg_hours_data['avg_h'] is not None else 0.0

        team_stats = list(MaintenanceTeam.objects.annotate(
            total_reqs=Count('assigned_requests'),
            completed_reqs=Count('assigned_requests', filter=Q(assigned_requests__status__in=['completed', 'repaired']))
        ).values('name', 'total_reqs', 'completed_reqs'))

        category_stats = list(Equipment.objects.values('category').annotate(
            equipment_count=Count('id'),
            request_count=Count('maintenance_requests')
        ).order_by('-request_count'))
        for item in category_stats:
            if not item['category']:
                item['category'] = 'General'

        type_stats = list(MaintenanceRequest.objects.values('request_type').annotate(
            count=Count('id')
        ))

        status_stats = list(MaintenanceRequest.objects.values('status').annotate(
            count=Count('id')
        ))

        priority_stats = list(MaintenanceRequest.objects.values('priority').annotate(
            count=Count('id')
        ))

        now = timezone.now().date()
        months = []
        for i in range(5, -1, -1):
            m = (now.month - i - 1) % 12 + 1
            y = now.year + ((now.month - i - 1) // 12)
            months.append((y, m))

        monthly_trends = []
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for y, m in months:
            opened = MaintenanceRequest.objects.filter(created_at__year=y, created_at__month=m).count()
            resolved = MaintenanceRequest.objects.filter(completed_date__year=y, completed_date__month=m, status__in=['completed', 'repaired']).count()
            monthly_trends.append({
                'month': f"{month_names[m-1]}",
                'opened': opened,
                'resolved': resolved
            })

        return JsonResponse({
            'kpis': {
                'total_requests': total_requests,
                'completed_count': completed_count,
                'open_count': open_count,
                'scrap_count': scrap_count,
                'sla_compliance': f"{sla_compliance}%",
                'avg_resolution': f"{avg_resolution_hours}h"
            },
            'by_team': team_stats,
            'by_category': category_stats,
            'by_type': type_stats,
            'by_status': status_stats,
            'by_priority': priority_stats,
            'monthly_trends': monthly_trends
        })

    return render(request, 'analytics.html')


@login_required
def settings_view(request):
    return render(request, 'settings.html')


@login_required
def calendar_view(request):
    preventive_requests = MaintenanceRequest.objects.filter(
        request_type='preventive',
        scheduled_date__isnull=False
    ).select_related('equipment', 'assigned_team', 'assigned_technician')
    
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        events = [{
            'id': req.id,
            'title': req.title,
            'description': req.description,
            'equipment_id': req.equipment.id,
            'equipment_name': req.equipment.name,
            'equipment_serial': req.equipment.serial_number,
            'assigned_team_id': req.assigned_team.id if req.assigned_team else None,
            'team_name': req.assigned_team.name if req.assigned_team else '',
            'assigned_technician_id': req.assigned_technician.id if req.assigned_technician else None,
            'technician_name': req.assigned_technician.get_full_name() or req.assigned_technician.username if req.assigned_technician else '',
            'status': req.status,
            'priority': req.priority,
            'request_type': req.request_type,
            'duration_value': float(req.duration_value) if req.duration_value is not None else None,
            'duration_unit': req.duration_unit,
            'duration_display': req.duration_display,
            'scheduled_date': req.scheduled_date.isoformat() if req.scheduled_date else None,
            'is_overdue': req.is_overdue
        } for req in preventive_requests]
        return JsonResponse({'events': events})

    equipments = Equipment.objects.exclude(status='scrapped')
    teams = MaintenanceTeam.objects.all()
    technicians = User.objects.filter(user_type='technician')

    context = {
        'preventive_requests': preventive_requests,
        'equipments': equipments,
        'teams': teams,
        'technicians': technicians,
    }
    return render(request, 'calendar.html', context)

