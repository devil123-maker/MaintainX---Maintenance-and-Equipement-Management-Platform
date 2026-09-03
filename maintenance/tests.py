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

        # Test Scrap status setting
        response_scrap = self.client.put(
            reverse('request_detail', kwargs={'pk': self.request.pk}),
            data=json.dumps({'status': 'scrap'}),
            content_type='application/json'
        )
        self.assertEqual(response_scrap.status_code, 200)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'scrap')
