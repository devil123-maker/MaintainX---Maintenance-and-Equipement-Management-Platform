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
