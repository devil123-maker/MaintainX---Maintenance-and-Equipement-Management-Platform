from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Count, Avg
import json
from django.utils import timezone
from .models import MaintenanceTeam, MaintenanceRequest, MaintenanceHistory
from equipment.models import Equipment
from accounts.models import User


@login_required
@require_http_methods(["POST"])
def request_join(request, pk):
    """
    Dedicated atomic action for eligible technicians to claim/join an unassigned NEW request.
    Enforces row locking with select_for_update() to prevent race conditions.
    """
    user = request.user
    is_elevated = user.is_staff or user.is_superuser or user.user_type in ['admin', 'manager']
    if not (user.is_technician_user or is_elevated):
        return JsonResponse({
            'success': False,
            'error': 'Permission denied. Only technicians can join maintenance requests.'
        }, status=403)

    with transaction.atomic():
        try:
            maintenance_request = MaintenanceRequest.objects.select_for_update().get(pk=pk)
        except MaintenanceRequest.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Maintenance request not found.'
            }, status=404)

        if maintenance_request.equipment and maintenance_request.equipment.status == 'scrapped':
            return JsonResponse({
                'success': False,
                'error': 'Cannot join request for scrapped equipment.'
            }, status=400)

        if maintenance_request.assigned_technician_id is not None:
            return JsonResponse({
                'success': False,
                'error': 'This request has already been claimed by another technician.'
            }, status=409)

        if maintenance_request.status not in ['new', 'pending']:
            return JsonResponse({
                'success': False,
                'error': f"Cannot join request with status '{maintenance_request.status}'."
            }, status=400)

        if not maintenance_request.assigned_team:
            return JsonResponse({
                'success': False,
                'error': 'This request does not have an assigned maintenance team.'
            }, status=400)

        is_member = maintenance_request.assigned_team.members.filter(pk=user.pk).exists()
        is_leader = maintenance_request.assigned_team.leader_id == user.pk

        if not (is_member or is_leader or is_elevated):
            return JsonResponse({
                'success': False,
                'error': 'Permission denied. You are not a member of the maintenance team for this request.'
            }, status=403)

        maintenance_request.assigned_technician = user
        maintenance_request.status = 'in_progress'
        try:
            maintenance_request.save()
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': e.message_dict if hasattr(e, 'message_dict') else str(e)
            }, status=400)

        tech_name = maintenance_request.assigned_technician.get_full_name() or maintenance_request.assigned_technician.first_name or maintenance_request.assigned_technician.username
        return JsonResponse({
            'success': True,
            'message': 'Request joined successfully.',
            'id': maintenance_request.id,
            'status': maintenance_request.status,
            'assigned_technician': maintenance_request.assigned_technician.id,
            'assigned_technician_name': tech_name,
            'request': {
                'id': maintenance_request.id,
                'title': maintenance_request.title,
                'status': maintenance_request.status,
                'assigned_technician': maintenance_request.assigned_technician.id,
                'assigned_technician_name': tech_name,
                'assigned_team': maintenance_request.assigned_team.name if maintenance_request.assigned_team else '',
                'priority': maintenance_request.priority,
                'equipment_name': maintenance_request.equipment.name if maintenance_request.equipment else ''
            }
        }, status=200)


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
        
        user = request.user
        if user.is_staff or user.is_superuser or user.user_type in ['admin', 'manager']:
            requests = MaintenanceRequest.objects.all()
        elif user.is_technician_user:
            requests = MaintenanceRequest.objects.filter(
                Q(assigned_team__members=user) |
                Q(assigned_team__leader=user) |
                Q(assigned_technician=user) |
                Q(requested_by=user)
            ).distinct()
        elif user.is_customer_user:
            requests = MaintenanceRequest.objects.filter(requested_by=user)
        else:
            requests = MaintenanceRequest.objects.filter(requested_by=user)
        
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
        user = request.user
        is_elevated = user.is_staff or user.is_superuser or user.user_type in ['admin', 'manager']
        data = json.loads(request.body)

        # Block technicians from creating normal customer corrective tickets
        if user.is_technician_user and not is_elevated:
            if data.get('request_type', 'corrective') == 'corrective':
                return JsonResponse({'error': 'Permission denied. Technicians cannot create customer corrective tickets.'}, status=403)

        if user.is_customer_user and data.get('assigned_technician'):
            return JsonResponse({'error': 'Customers cannot assign technicians.'}, status=403)
        try:
            equipment = get_object_or_404(Equipment, id=data['equipment'])
            if equipment.status == 'scrapped':
                return JsonResponse({'error': {'equipment': ['Cannot create a new maintenance request for scrapped equipment.']}}, status=400)

            # Customer corrective request: team derived from equipment, tech unassigned
            if user.is_customer_user:
                assigned_team_id = equipment.maintenance_team_id
                assigned_technician_id = None
                initial_status = 'new'
            else:
                assigned_team_id = data.get('assigned_team') or equipment.maintenance_team_id
                assigned_technician_id = data.get('assigned_technician')
                initial_status = data.get('status', 'new')

            maintenance_request = MaintenanceRequest.objects.create(
                title=data['title'],
                description=data['description'],
                equipment=equipment,
                requested_by=request.user,
                priority=data.get('priority', 'medium'),
                request_type=data.get('request_type', 'corrective'),
                scheduled_date=data.get('scheduled_date'),
                duration_hours=data.get('duration_hours'),
                duration_value=data.get('duration_value'),
                duration_unit=data.get('duration_unit', 'minutes'),
                assigned_team_id=assigned_team_id,
                assigned_technician_id=assigned_technician_id,
                status=initial_status
            )
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
            'can_join': maintenance_request.can_technician_join(request.user),
            'created_at': maintenance_request.created_at,
            'updated_at': maintenance_request.updated_at
        }
        wants_html = (
            request.headers.get('Sec-Fetch-Dest') == 'document' or
            request.headers.get('Sec-Fetch-Mode') == 'navigate' or
            request.GET.get('view') == 'html' or
            request.GET.get('format') == 'html'
        )
        if wants_html:
            user = request.user
            is_elevated = user.is_staff or user.is_superuser or user.user_type in ['admin', 'manager']
            user_teams = set()
            if user.is_technician_user:
                user_teams = set(user.teams.values_list('id', flat=True)) | set(user.led_teams.values_list('id', flat=True))
            is_team_member = maintenance_request.assigned_team_id in user_teams if maintenance_request.assigned_team_id else False

            user_can_join = (
                user.is_technician_user and
                maintenance_request.status in ['new', 'pending'] and
                maintenance_request.assigned_technician_id is None and
                is_team_member and
                (not maintenance_request.equipment or maintenance_request.equipment.status != 'scrapped')
            )
            user_is_assigned = (maintenance_request.assigned_technician_id == user.id)
            user_can_repair = (user_is_assigned or is_elevated)
            history = maintenance_request.history.select_related('performed_by').order_by('-created_at')

            context = {
                'maintenance_request': maintenance_request,
                'req': maintenance_request,
                'user_can_join': user_can_join,
                'user_is_assigned': user_is_assigned,
                'user_can_repair': user_can_repair,
                'history': history,
            }
            return render(request, 'ticket_detail.html', context)

        return JsonResponse(data)
    
    elif request.method == 'PUT':
        if not request.user.can_edit_request(maintenance_request):
            return JsonResponse({'error': 'Permission denied. You are not authorized to update this request.'}, status=403)
        data = json.loads(request.body)
        is_elevated = request.user.is_staff or request.user.is_superuser or request.user.user_type in ['admin', 'manager']

        # Guard 1: Customer cannot change status, team, technician
        if request.user.is_customer_user:
            if 'status' in data or 'assigned_technician' in data or 'assigned_team' in data:
                return JsonResponse({'error': 'Permission denied. Customers cannot change ticket status, team, or technician.'}, status=403)

        # Guard 2: Generic PUT cannot reassign technician unless manager/admin
        if 'assigned_technician' in data and not is_elevated:
            return JsonResponse({'error': 'Permission denied. Technicians must use the Join Request action.'}, status=403)

        # Guard 3: Moving to in_progress
        if data.get('status') == 'in_progress':
            target_tech = data.get('assigned_technician') or maintenance_request.assigned_technician_id
            if not target_tech:
                return JsonResponse({'error': 'Cannot move unassigned request to In Progress. Please use the Join Request button.'}, status=400)
            if not is_elevated and maintenance_request.assigned_technician_id and maintenance_request.assigned_technician_id != request.user.id:
                return JsonResponse({'error': 'Permission denied. This ticket is assigned to another technician.'}, status=403)

        # Guard 4: Repaired / completed transitions
        if data.get('status') in ['repaired', 'completed']:
            is_assigned_tech = (maintenance_request.assigned_technician_id == request.user.id)
            if not (is_assigned_tech or is_elevated):
                return JsonResponse({'error': 'Permission denied. Only the assigned technician or an authorized manager can mark this request as repaired.'}, status=403)

        # Guard 5: Scrap transitions
        if data.get('status') == 'scrap' and not is_elevated:
            return JsonResponse({'error': 'Permission denied. Only managers or admins can scrap equipment.'}, status=403)

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
                if not is_elevated:
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
            if maintenance_request.assigned_technician_id:
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
    is_assigned_tech = (maintenance_request.assigned_technician_id == request.user.id)
    is_elevated = request.user.is_staff or request.user.is_superuser or request.user.user_type in ['admin', 'manager']
    is_json = (
        request.content_type == 'application/json' or
        (request.body and request.body.startswith(b'{')) or
        request.headers.get('Accept') == 'application/json'
    )
    if not (is_assigned_tech or is_elevated):
        if is_json:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied. Only the assigned technician or a manager can mark this request as repaired.'
            }, status=403)
        return HttpResponseForbidden('Permission denied. Only the assigned technician or a manager can mark this request as repaired.')

    if request.method == 'POST':
        if is_json:
            data = json.loads(request.body) if request.body else {}
        else:
            data = request.POST.dict()

        if maintenance_request.status != 'in_progress':
            err_msg = f"Cannot complete a request that is in '{maintenance_request.status}' status. It must be in progress."
            if is_json:
                return JsonResponse({
                    'success': False,
                    'error': err_msg
                }, status=400)
            from django.contrib import messages
            messages.error(request, err_msg)
            return redirect('request_detail', pk=maintenance_request.id)

        try:
            target_status = data.get('status') or 'repaired'
            maintenance_request.status = target_status
            maintenance_request.completed_date = timezone.now().date()
            if data.get('duration_hours') is not None and data.get('duration_hours') != '':
                maintenance_request.duration_hours = data['duration_hours']
            if data.get('duration_value') is not None and data.get('duration_value') != '':
                maintenance_request.duration_value = data['duration_value']
            if data.get('duration_unit'):
                maintenance_request.duration_unit = data['duration_unit']
            maintenance_request.save()
            
            notes = data.get('notes') or 'Completed by assigned technician'
            cost = data.get('cost') or None
            if cost == '':
                cost = None
            parts_used = data.get('parts_used', '')
            MaintenanceHistory.objects.create(
                maintenance_request=maintenance_request,
                performed_by=request.user,
                notes=notes,
                cost=cost,
                parts_used=parts_used
            )
            
            if is_json:
                return JsonResponse({
                    'success': True,
                    'message': 'Maintenance request completed',
                    'status': maintenance_request.status
                })
            from django.contrib import messages
            messages.success(request, f"Request TKT-{maintenance_request.id} has been marked as repaired.")
            return redirect('request_detail', pk=maintenance_request.id)
        except ValidationError as e:
            if is_json:
                return JsonResponse({
                    'success': False,
                    'error': e.message_dict if hasattr(e, 'message_dict') else str(e)
                }, status=400)
            from django.contrib import messages
            messages.error(request, str(e))
            return redirect('request_detail', pk=maintenance_request.id)


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
@ensure_csrf_cookie
def tickets_view(request):
    equipment_id = request.GET.get('equipment')
    tab = request.GET.get('tab')
    user = request.user

    if user.is_staff or user.is_superuser or user.user_type in ['admin', 'manager']:
        requests = MaintenanceRequest.objects.all()
    elif user.is_technician_user:
        requests = MaintenanceRequest.objects.filter(
            Q(assigned_team__members=user) |
            Q(assigned_team__leader=user) |
            Q(assigned_technician=user) |
            Q(requested_by=user)
        ).distinct()
    elif user.is_customer_user:
        requests = MaintenanceRequest.objects.filter(requested_by=user)
    else:
        requests = MaintenanceRequest.objects.filter(requested_by=user)

    if tab == 'available' and user.is_technician_user:
        requests = requests.filter(status__in=['new', 'pending'], assigned_technician__isnull=True).exclude(equipment__status='scrapped')
    elif tab == 'active' and user.is_technician_user:
        requests = requests.filter(status='in_progress', assigned_technician=user)
    elif tab == 'completed':
        requests = requests.filter(status__in=['completed', 'repaired'])

    requests = requests.select_related(
        'equipment', 'assigned_team', 'assigned_technician', 'requested_by'
    ).order_by('-created_at')

    if equipment_id:
        requests = requests.filter(equipment_id=equipment_id)

    requests_list = list(requests)
    user_teams = set()
    if user.is_technician_user:
        user_teams = set(user.teams.values_list('id', flat=True)) | set(user.led_teams.values_list('id', flat=True))
    is_elevated = user.is_staff or user.is_superuser or user.user_type in ['admin', 'manager']

    for req in requests_list:
        is_team_member = req.assigned_team_id in user_teams if req.assigned_team_id else False
        req.user_can_join = (
            user.is_technician_user and
            req.status in ['new', 'pending'] and
            req.assigned_technician_id is None and
            is_team_member and
            (not req.equipment or req.equipment.status != 'scrapped')
        )
        req.user_is_assigned = (req.assigned_technician_id == user.id)
        req.user_can_repair = (req.user_is_assigned or is_elevated)

    return render(request, 'tickets.html', {
        'requests': requests_list,
        'selected_equipment_id': equipment_id,
        'active_tab': tab
    })


@login_required
def create_ticket_view(request):
    user = request.user
    is_elevated = user.is_staff or user.is_superuser or user.user_type in ['admin', 'manager']
    if user.is_technician_user and not is_elevated:
        return HttpResponseForbidden("Permission denied. Technicians cannot create customer maintenance requests.")

    selected_equipment_id = request.GET.get('equipment')
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        equipment_id = request.POST.get('equipment')
        priority = request.POST.get('priority', 'medium')
        request_type = request.POST.get('request_type', 'corrective')
        scheduled_date = request.POST.get('scheduled_date')
        duration_hours = request.POST.get('duration_hours')
        duration_value = request.POST.get('duration_value')
        duration_unit = request.POST.get('duration_unit', 'minutes')
        
        if title and description and equipment_id:
            try:
                equipment = get_object_or_404(Equipment, id=equipment_id)
                if user.is_customer_user:
                    assigned_team_id = equipment.maintenance_team_id
                    assigned_technician_id = None
                else:
                    assigned_team_id = request.POST.get('assigned_team') or equipment.maintenance_team_id
                    assigned_technician_id = request.POST.get('assigned_technician') or None

                MaintenanceRequest.objects.create(
                    title=title,
                    description=description,
                    equipment_id=equipment_id,
                    requested_by=request.user,
                    priority=priority,
                    request_type=request_type,
                    status='new',
                    scheduled_date=scheduled_date if scheduled_date else None,
                    assigned_team_id=assigned_team_id,
                    assigned_technician_id=assigned_technician_id,
                    duration_hours=duration_hours if duration_hours else None,
                    duration_value=duration_value if duration_value else None,
                    duration_unit=duration_unit
                )
                return redirect('tickets')
            except ValidationError as e:
                equipments = Equipment.objects.exclude(status='scrapped')
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
            
    equipments = Equipment.objects.exclude(status='scrapped')
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

        tech_stats_raw = list(MaintenanceRequest.objects.values('assigned_technician__first_name', 'assigned_technician__username').annotate(
            count=Count('id')
        ))
        tech_stats = []
        for item in tech_stats_raw:
            name = item.get('assigned_technician__first_name') or item.get('assigned_technician__username') or 'Unassigned'
            tech_stats.append({'technician': name, 'count': item['count']})

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
            'by_technician': tech_stats,
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

