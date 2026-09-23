from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from equipment.models import Equipment
import json

User = get_user_model()

class EquipmentTests(TestCase):
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
            name='Test Generator',
            serial_number='SN-1001',
            status='active',
            created_by=self.user
        )

    def test_equipment_list_get(self):
        response = self.client.get(reverse('equipment_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('equipment', data)
        self.assertEqual(len(data['equipment']), 1)

    def test_equipment_create_post(self):
        response = self.client.post(
            reverse('equipment_list'),
            data=json.dumps({
                'name': 'HVAC Unit',
                'serial_number': 'SN-2002',
                'status': 'active'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Equipment.objects.filter(serial_number='SN-2002').exists())

    def test_equipment_detail_get(self):
        response = self.client.get(reverse('equipment_detail', kwargs={'pk': self.equipment.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Test Generator')

    def test_equipment_update_put(self):
        response = self.client.put(
            reverse('equipment_detail', kwargs={'pk': self.equipment.pk}),
            data=json.dumps({'name': 'Updated Generator'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.name, 'Updated Generator')

    def test_equipment_delete(self):
        response = self.client.delete(reverse('equipment_detail', kwargs={'pk': self.equipment.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Equipment.objects.filter(pk=self.equipment.pk).exists())

    def test_equipment_phase2_fields(self):
        from maintenance.models import MaintenanceTeam
        team = MaintenanceTeam.objects.create(name='Alpha Maintenance Team', leader=self.user)
        employee = User.objects.create_user(
            username='emp@example.com',
            email='emp@example.com',
            password='password123',
            user_type='customer'
        )
        response = self.client.post(
            reverse('equipment_list'),
            data=json.dumps({
                'name': 'CNC Lathe Machine',
                'serial_number': 'CNC-9900',
                'category': 'Machinery',
                'department': 'Manufacturing',
                'warranty_expiry_date': '2028-12-31',
                'assigned_employee': employee.id,
                'maintenance_team': team.id,
                'default_technician': self.user.id,
                'status': 'active'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        eq = Equipment.objects.get(serial_number='CNC-9900')
        self.assertEqual(eq.category, 'Machinery')
        self.assertEqual(eq.department, 'Manufacturing')
        self.assertEqual(eq.assigned_employee, employee)
        self.assertEqual(eq.maintenance_team, team)
        self.assertEqual(eq.default_technician, self.user)

    def test_equipment_scrapped_status(self):
        response = self.client.put(
            reverse('equipment_detail', kwargs={'pk': self.equipment.pk}),
            data=json.dumps({'status': 'scrapped'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.status, 'scrapped')

    def test_equipment_maintenance_count(self):
        from maintenance.models import MaintenanceRequest
        MaintenanceRequest.objects.create(
            title='Fix generator oil',
            description='Oil change',
            equipment=self.equipment,
            requested_by=self.user,
            status='pending'
        )
        MaintenanceRequest.objects.create(
            title='Replace filter',
            description='Filter replacement',
            equipment=self.equipment,
            requested_by=self.user,
            status='repaired'
        )

        self.assertEqual(self.equipment.maintenance_count, 2)
        self.assertEqual(self.equipment.open_maintenance_count, 1)

    def test_equipment_maintenance_filtering(self):
        from maintenance.models import MaintenanceRequest
        eq2 = Equipment.objects.create(
            name='Compressor B',
            serial_number='COMP-5500',
            status='active',
            created_by=self.user
        )
        req1 = MaintenanceRequest.objects.create(
            title='Gen repair',
            description='Repair gen',
            equipment=self.equipment,
            requested_by=self.user
        )
        req2 = MaintenanceRequest.objects.create(
            title='Compressor check',
            description='Check compressor',
            equipment=eq2,
            requested_by=self.user
        )

        response = self.client.get(reverse('equipment_maintenance', kwargs={'pk': self.equipment.pk}), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        req_ids = [r['id'] for r in data['requests']]
        self.assertIn(req1.id, req_ids)
        self.assertNotIn(req2.id, req_ids)
        self.assertEqual(data['total_requests'], 1)

    def test_equipment_maintenance_html_render(self):
        response = self.client.get(reverse('equipment_list'), HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'equipment.html')

        response_maint = self.client.get(reverse('equipment_maintenance', kwargs={'pk': self.equipment.pk}), HTTP_ACCEPT='text/html')
        self.assertEqual(response_maint.status_code, 200)
        self.assertTemplateUsed(response_maint, 'equipment_maintenance.html')
