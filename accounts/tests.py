from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')

    def test_signup_success(self):
        response = self.client.post(self.signup_url, {
            'full_name': 'Test User',
            'mobile_number': '1234567890',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'user_type': 'technician'
        })
        self.assertRedirects(response, self.login_url)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_signup_password_mismatch(self):
        response = self.client.post(self.signup_url, {
            'full_name': 'Test User',
            'mobile_number': '1234567890',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'different_password',
            'user_type': 'technician'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='test@example.com').exists())

    def test_login_success(self):
        user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='password123',
            first_name='Test User',
            user_type='technician'
        )
        response = self.client.post(self.login_url, {
            'email': 'user@example.com',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_failure(self):
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)

    def test_password_reset_page_loads(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_post_sends_mail(self):
        from django.core import mail
        user = User.objects.create_user(
            username='reset@example.com',
            email='reset@example.com',
            password='oldpassword123'
        )
        response = self.client.post(reverse('password_reset'), {'email': 'reset@example.com'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('MaintainX', mail.outbox[0].subject)

    def test_login_remember_me_checked(self):
        user = User.objects.create_user(
            username='remember@example.com',
            email='remember@example.com',
            password='password123'
        )
        response = self.client.post(self.login_url, {
            'email': 'remember@example.com',
            'password': 'password123',
            'remember': 'on'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(self.client.session.get_expiry_age(), 1209600)
        self.assertIn('remembered_email', response.cookies)
        self.assertEqual(response.cookies['remembered_email'].value, 'remember@example.com')

    def test_login_remember_me_unchecked(self):
        user = User.objects.create_user(
            username='noremember@example.com',
            email='noremember@example.com',
            password='password123'
        )
        response = self.client.post(self.login_url, {
            'email': 'noremember@example.com',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_prefills_remembered_email(self):
        self.client.cookies['remembered_email'] = 'saved@example.com'
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'saved@example.com')
        self.assertContains(response, 'checked')

    def test_user_roles_and_permission_helpers(self):
        admin = User.objects.create_user(username='admin', email='admin@ex.com', user_type='admin', is_staff=True)
        tech = User.objects.create_user(username='tech', email='tech@ex.com', user_type='technician')
        cust = User.objects.create_user(username='cust', email='cust@ex.com', user_type='customer')

        self.assertTrue(admin.is_admin_user)
        self.assertTrue(admin.can_manage_equipment)
        self.assertTrue(admin.can_assign_requests)

        self.assertTrue(tech.is_technician_user)
        self.assertTrue(tech.can_manage_equipment)

        self.assertTrue(cust.is_customer_user)
        self.assertFalse(cust.can_manage_equipment)



