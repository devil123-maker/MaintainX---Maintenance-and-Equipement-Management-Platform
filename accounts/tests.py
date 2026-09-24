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
        self.assertTrue('GearGuard' in mail.outbox[0].subject or 'MaintainX' in mail.outbox[0].subject)

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

    def test_case_1_new_registration_login_is_empty(self):
        # Simulate browser having a previous cookie from another user
        self.client.cookies['remembered_email'] = 'previous_user@example.com'
        response = self.client.post(self.signup_url, {
            'full_name': 'Dev Patel',
            'mobile_number': '9876543210',
            'email': 'dev@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'user_type': 'technician'
        })
        self.assertRedirects(response, self.login_url)
        # Login page rendered
        login_page = self.client.get(self.login_url)
        self.assertEqual(login_page.status_code, 200)
        # Email field must be empty (not dev@example.com, not previous_user@example.com)
        self.assertNotContains(login_page, 'value="dev@example.com"')
        self.assertNotContains(login_page, 'value="previous_user@example.com"')
        self.assertContains(login_page, 'value=""')
        # Remember Me must be unchecked
        self.assertNotContains(login_page, 'name="remember" checked')

    def test_case_2_login_without_remember_me_logout_is_empty(self):
        user = User.objects.create_user(
            username='dev_no_rem@example.com',
            email='dev_no_rem@example.com',
            password='Password123!'
        )
        # Login with remember me UNCHECKED
        response = self.client.post(self.login_url, {
            'email': 'dev_no_rem@example.com',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard'))
        # User logs out
        logout_resp = self.client.get(reverse('logout'))
        self.assertRedirects(logout_resp, self.login_url)
        # Login page rendered
        login_page = self.client.get(self.login_url)
        self.assertEqual(login_page.status_code, 200)
        self.assertNotContains(login_page, 'value="dev_no_rem@example.com"')
        self.assertContains(login_page, 'value=""')
        self.assertNotContains(login_page, 'name="remember" checked')

    def test_case_3_login_with_remember_me_logout_restores_email(self):
        user = User.objects.create_user(
            username='dev_rem@example.com',
            email='dev_rem@example.com',
            password='Password123!'
        )
        # Login with remember me CHECKED
        response = self.client.post(self.login_url, {
            'email': 'dev_rem@example.com',
            'password': 'Password123!',
            'remember': 'on'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(self.client.session.get_expiry_age(), 1209600)
        # User logs out
        logout_resp = self.client.get(reverse('logout'))
        self.assertRedirects(logout_resp, self.login_url)
        # Login page rendered
        login_page = self.client.get(self.login_url)
        self.assertEqual(login_page.status_code, 200)
        # Email must be restored
        self.assertContains(login_page, 'value="dev_rem@example.com"')
        # Password must be empty in HTML (no plaintext password leak)
        self.assertContains(login_page, 'name="password" id="password" placeholder="Enter your password" required autocomplete="current-password" value=""')
        # Remember Me must be CHECKED
        self.assertContains(login_page, 'name="remember" id="remember" checked')

    def test_case_1_fresh_visit_login_is_empty(self):
        # Case 1: Fresh visit to login page (no cookies, clean browser/incognito)
        login_page = self.client.get(self.login_url)
        self.assertEqual(login_page.status_code, 200)
        self.assertContains(login_page, 'value=""')
        self.assertNotContains(login_page, 'name="remember" id="remember" checked')
        self.assertContains(login_page, 'name="password" id="password" placeholder="Enter your password" required autocomplete="current-password" value=""')

    def test_multi_user_isolation(self):
        # User A logs in with Remember Me
        user_a = User.objects.create_user(username='user_a@ex.com', email='user_a@ex.com', password='PasswordA123!')
        user_b = User.objects.create_user(username='user_b@ex.com', email='user_b@ex.com', password='PasswordB123!')

        resp_a = self.client.post(self.login_url, {'email': 'user_a@ex.com', 'password': 'PasswordA123!', 'remember': 'on'})
        self.assertRedirects(resp_a, reverse('dashboard'))
        self.client.get(reverse('logout'))

        # Now login page has user A's email remembered
        lp_after_a = self.client.get(self.login_url)
        self.assertContains(lp_after_a, 'value="user_a@ex.com"')
        self.assertContains(lp_after_a, 'name="remember" id="remember" checked')

        # User B now logs in WITHOUT Remember Me
        resp_b = self.client.post(self.login_url, {'email': 'user_b@ex.com', 'password': 'PasswordB123!'})
        self.assertRedirects(resp_b, reverse('dashboard'))
        self.client.get(reverse('logout'))

        # Login page must now be completely clean (no user A, no user B, unchecked)
        lp_after_b = self.client.get(self.login_url)
        self.assertNotContains(lp_after_b, 'value="user_a@ex.com"')
        self.assertNotContains(lp_after_b, 'value="user_b@ex.com"')
        self.assertNotContains(lp_after_b, 'name="remember" id="remember" checked')

    def test_login_page_refresh_consistency(self):
        # Refresh without remember me stays clean
        resp1 = self.client.get(self.login_url)
        resp2 = self.client.get(self.login_url)
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        self.assertNotContains(resp2, 'name="remember" id="remember" checked')

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



