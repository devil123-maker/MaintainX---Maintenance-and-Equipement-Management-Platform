from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from equipment.models import Equipment
from maintenance.models import MaintenanceTeam, MaintenanceRequest, MaintenanceHistory
import json

User = get_user_model()

class MaintenanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='tech@example.com',
            email='tech@example.com',
            password='password123',
            first_name='Tech',
            user_type='technician'
        )
        self.client.login(username='tech@example.com', password='password123')
        self.equipment = Equipment.objects.create(
            name='Test Pump',
            serial_number='SN-3003',
            status='active',
            created_by=self.user
        )
        self.team = MaintenanceTeam.objects.create(
            name='Alpha Team',
            leader=self.user
        )
        self.request = MaintenanceRequest.objects.create(
            title='Fix Pump Leak',
            description='Water leaking from valve',
            equipment=self.equipment,
            requested_by=self.user,
            priority='high'
        )

    def test_team_list(self):
        response = self.client.get(reverse('team_list'))
        self.assertEqual(response.status_code, 200)

    def test_team_create(self):
        response = self.client.post(
            reverse('team_list'),
            data=json.dumps({'name': 'Beta Team'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

    def test_request_list(self):
        response = self.client.get(reverse('request_list'))
        self.assertEqual(response.status_code, 200)

    def test_request_assign_team(self):
        response = self.client.post(
            reverse('request_assign_team', kwargs={'pk': self.request.pk}),
            data=json.dumps({'team_id': self.team.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.request.refresh_from_db()
        self.assertEqual(self.request.assigned_team, self.team)
        self.assertEqual(self.request.status, 'in_progress')

    def test_request_complete(self):
        response = self.client.post(
            reverse('request_complete', kwargs={'pk': self.request.pk}),
            data=json.dumps({'notes': 'Replaced seal', 'cost': 150.00}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'completed')
        self.assertTrue(MaintenanceHistory.objects.filter(maintenance_request=self.request).exists())

    def test_dashboard(self):
        response = self.client.get(reverse('dashboard'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('equipment_stats', data)
        self.assertIn('request_stats', data)

    def test_dashboard_html(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_phase3_request_fields_and_types(self):
        # Ensure user is in team for validation
        self.team.members.add(self.user)
        response = self.client.post(
            reverse('request_list'),
            data=json.dumps({
                'title': 'Monthly Preventive Service',
                'description': 'Routine filter replacement',
                'equipment': self.equipment.id,
                'request_type': 'preventive',
                'priority': 'medium',
                'scheduled_date': '2026-09-15',
                'duration_hours': 2.5,
                'assigned_technician': self.user.id,
                'assigned_team': self.team.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        req = MaintenanceRequest.objects.get(title='Monthly Preventive Service')
        self.assertEqual(req.request_type, 'preventive')
        self.assertEqual(req.assigned_technician, self.user)
        self.assertEqual(float(req.duration_hours), 2.5)

    def test_gearguard_statuses(self):
        response = self.client.put(
            reverse('request_detail', kwargs={'pk': self.request.pk}),
            data=json.dumps({'status': 'repaired'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'repaired')

    def test_autofill_team_and_default_technician(self):
        tech2 = User.objects.create_user(username='tech2@example.com', password='password123', user_type='technician')
        self.team.members.add(tech2)
        self.equipment.maintenance_team = self.team
        self.equipment.default_technician = tech2
        self.equipment.save()

        req = MaintenanceRequest.objects.create(
            title='Auto-fill Test Request',
            description='Testing auto-fill',
            equipment=self.equipment,
            requested_by=self.user
        )
        self.assertEqual(req.assigned_team, self.team)
        self.assertEqual(req.assigned_technician, tech2)

    def test_technician_membership_validation(self):
        other_tech = User.objects.create_user(username='other@example.com', password='password123', user_type='technician')
        from django.core.exceptions import ValidationError
        req = MaintenanceRequest(
            title='Invalid Tech Request',
            description='Tech not in team',
            equipment=self.equipment,
            requested_by=self.user,
            assigned_team=self.team,
            assigned_technician=other_tech
        )
        with self.assertRaises(ValidationError):
            req.full_clean()

    def test_equipment_team_mismatch_validation(self):
        team2 = MaintenanceTeam.objects.create(name='Beta Team', leader=self.user)
        self.equipment.maintenance_team = self.team
        self.equipment.save()
        from django.core.exceptions import ValidationError
        req = MaintenanceRequest(
            title='Team Mismatch Request',
            description='Team mismatch',
            equipment=self.equipment,
            requested_by=self.user,
            assigned_team=team2
        )
        with self.assertRaises(ValidationError):
            req.full_clean()

    def test_scrapped_equipment_protection(self):
        self.equipment.status = 'scrapped'
        self.equipment.save()
        from django.core.exceptions import ValidationError
        req = MaintenanceRequest(
            title='Scrapped Equipment Request',
            description='Cannot create for scrapped equipment',
            equipment=self.equipment,
            requested_by=self.user
        )
        with self.assertRaises(ValidationError):
            req.full_clean()

    def test_scrap_updates_equipment_status(self):
        req = MaintenanceRequest.objects.create(
            title='Scrap Test Request',
            description='Testing scrap automation',
            equipment=self.equipment,
            requested_by=self.user,
            status='in_progress'
        )
        req.status = 'scrap'
        req.save()
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.status, 'scrapped')

    def test_terminal_status_transition_rejection(self):
        req = MaintenanceRequest.objects.create(
            title='Terminal Status Request',
            description='Testing terminal status protection',
            equipment=self.equipment,
            requested_by=self.user,
            status='repaired'
        )
        from django.core.exceptions import ValidationError
        req.status = 'in_progress'
        with self.assertRaises(ValidationError):
            req.full_clean()

    def test_dynamic_overdue_property(self):
        import datetime
        from django.utils import timezone
        today = timezone.now().date()
        past_date = today - datetime.timedelta(days=5)
        future_date = today + datetime.timedelta(days=5)

        req_overdue = MaintenanceRequest.objects.create(
            title='Overdue Request',
            description='Scheduled in past',
            equipment=self.equipment,
            requested_by=self.user,
            status='pending',
            scheduled_date=past_date
        )
        self.assertTrue(req_overdue.is_overdue)

        req_repaired = MaintenanceRequest.objects.create(
            title='Repaired Request',
            description='Past date but repaired',
            equipment=self.equipment,
            requested_by=self.user,
            status='repaired',
            scheduled_date=past_date
        )
        self.assertFalse(req_repaired.is_overdue)

        req_future = MaintenanceRequest.objects.create(
            title='Future Request',
            description='Scheduled in future',
            equipment=self.equipment,
            requested_by=self.user,
            status='pending',
            scheduled_date=future_date
        )
        self.assertFalse(req_future.is_overdue)

    def test_kanban_view_render(self):
        response = self.client.get(reverse('tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'kanban-board')
        self.assertContains(response, 'kanban-column')

    def test_kanban_status_update_api_success(self):
        response = self.client.put(
            reverse('request_detail', kwargs={'pk': self.request.pk}),
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'in_progress')

    def test_kanban_status_update_api_rejection(self):
        self.request.status = 'repaired'
        self.request.save()

        response = self.client.put(
            reverse('request_detail', kwargs={'pk': self.request.pk}),
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'repaired')

    def test_kanban_scrap_status_update_triggers_equipment_scrapped(self):
        response = self.client.put(
            reverse('request_detail', kwargs={'pk': self.request.pk}),
            data=json.dumps({'status': 'scrap'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.status, 'scrapped')

    def test_calendar_view_render(self):
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')

    def test_calendar_api_preventive_filtering(self):
        # Create a corrective request (should NOT appear on preventive calendar)
        MaintenanceRequest.objects.create(
            title='Breakdown Urgent Repair',
            description='Motor failed',
            equipment=self.equipment,
            requested_by=self.user,
            request_type='corrective',
            scheduled_date='2026-09-20'
        )
        # Create a preventive request (SHOULD appear)
        prev_req = MaintenanceRequest.objects.create(
            title='Monthly Gearbox Inspection',
            description='Routine preventive check',
            equipment=self.equipment,
            requested_by=self.user,
            request_type='preventive',
            scheduled_date='2026-09-22'
        )

        response = self.client.get(reverse('calendar'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        event_titles = [e['title'] for e in data['events']]
        self.assertIn('Monthly Gearbox Inspection', event_titles)
        self.assertNotIn('Breakdown Urgent Repair', event_titles)

    def test_calendar_reschedule_api(self):
        prev_req = MaintenanceRequest.objects.create(
            title='Reschedule Target',
            description='Rescheduling test',
            equipment=self.equipment,
            requested_by=self.user,
            request_type='preventive',
            scheduled_date='2026-09-10'
        )
        response = self.client.put(
            reverse('request_detail', kwargs={'pk': prev_req.pk}),
            data=json.dumps({'scheduled_date': '2026-09-25'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        prev_req.refresh_from_db()
        self.assertEqual(str(prev_req.scheduled_date), '2026-09-25')

    def test_calendar_scrapped_equipment_protection(self):
        self.equipment.status = 'scrapped'
        self.equipment.save()

        response = self.client.post(
            reverse('request_list'),
            data=json.dumps({
                'title': 'Preventive on Scrapped Machine',
                'description': 'Should fail',
                'equipment': self.equipment.id,
                'request_type': 'preventive',
                'scheduled_date': '2026-09-28'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_dynamic_duration_minutes(self):
        req = MaintenanceRequest.objects.create(
            title='Laptop quick fix',
            description='Fixed cable in 10 mins',
            equipment=self.equipment,
            requested_by=self.user,
            duration_value=10,
            duration_unit='minutes'
        )
        self.assertEqual(req.duration_display, '10 mins')
        self.assertEqual(float(req.duration_hours), 0.17)

    def test_dynamic_duration_hours(self):
        req = MaintenanceRequest.objects.create(
            title='Pump inspection',
            description='Took 2.5 hours',
            equipment=self.equipment,
            requested_by=self.user,
            duration_value=2.5,
            duration_unit='hours'
        )
        self.assertEqual(req.duration_display, '2.5 hrs')
        self.assertEqual(float(req.duration_hours), 2.5)

    def test_dynamic_duration_days(self):
        req = MaintenanceRequest.objects.create(
            title='Overhaul',
            description='Took 1 day',
            equipment=self.equipment,
            requested_by=self.user,
            duration_value=1,
            duration_unit='days'
        )
        self.assertEqual(req.duration_display, '1 day')
        self.assertEqual(float(req.duration_hours), 24.0)

    def test_calendar_modal_cancel_button_semantics(self):
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-modal-close')
        self.assertContains(response, 'type="button"')
        self.assertContains(response, 'onclick="closeModal(this)"')

