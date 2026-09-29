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

    def test_login_page_renders_continue_with_google_button(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue with Google')
        self.assertContains(response, '/accounts/google/login/')

    def test_signup_page_renders_continue_with_google_button(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue with Google')
        self.assertContains(response, '/accounts/google/login/')

    def test_google_oauth_urls_resolved(self):
        from django.urls import resolve
        login_match = resolve('/accounts/google/login/')
        callback_match = resolve('/accounts/google/login/callback/')
        self.assertIsNotNone(login_match)
        self.assertIsNotNone(callback_match)

    def test_custom_social_account_adapter_new_user_role_is_customer(self):
        from accounts.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        adapter = CustomSocialAccountAdapter()
        new_user = User(username='googleuser@example.com', email='googleuser@example.com')
        socialaccount = SocialAccount(provider='google', uid='123456789', extra_data={'name': 'Google User', 'email': 'googleuser@example.com'})
        sociallogin = SocialLogin(user=new_user, account=socialaccount)

        populated_user = adapter.populate_user(
            request=None,
            sociallogin=sociallogin,
            data={'email': 'googleuser@example.com', 'name': 'Google User'}
        )
        self.assertEqual(populated_user.user_type, 'customer')
        self.assertTrue(populated_user.is_customer_user)
        self.assertFalse(populated_user.is_technician_user)
        self.assertEqual(populated_user.first_name, 'Google User')

    def test_custom_social_account_adapter_existing_technician_preserves_role(self):
        from accounts.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        existing_tech = User.objects.create_user(
            username='tech_google@example.com',
            email='tech_google@example.com',
            password='password123',
            user_type='technician',
            first_name='Existing Technician'
        )
        adapter = CustomSocialAccountAdapter()
        socialaccount = SocialAccount(user=existing_tech, provider='google', uid='987654321', extra_data={'name': 'Existing Technician'})
        sociallogin = SocialLogin(user=existing_tech, account=socialaccount)

        populated_user = adapter.populate_user(
            request=None,
            sociallogin=sociallogin,
            data={'email': 'tech_google@example.com'}
        )
        self.assertEqual(populated_user.user_type, 'technician')
        self.assertTrue(populated_user.is_technician_user)
        self.assertFalse(populated_user.is_customer_user)

    def test_google_provider_scopes_and_settings(self):
        from django.conf import settings
        self.assertIn('allauth.socialaccount.providers.google', settings.INSTALLED_APPS)
        self.assertIn('allauth.account.auth_backends.AuthenticationBackend', settings.AUTHENTICATION_BACKENDS)
        self.assertEqual(settings.SITE_ID, 1)
        google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        self.assertIn('SCOPE', google_config)
        self.assertEqual(google_config['SCOPE'], ['profile', 'email'])

    def test_jwt_and_jwtkit_available(self):
        import jwt
        from allauth.socialaccount.internal import jwtkit
        self.assertTrue(hasattr(jwt, 'decode'))
        self.assertTrue(hasattr(jwtkit, 'verify_and_decode'))

    def test_social_signup_form_customer_role(self):
        from accounts.forms import SocialSignupForm
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        from django.test import RequestFactory
        sa = SocialAccount(provider='google', uid='test_cust_uid', extra_data={'email': 'new_cust@example.com', 'name': 'New Cust'})
        sl = SocialLogin(user=User(email='new_cust@example.com', username='new_cust@example.com'), account=sa)
        form = SocialSignupForm(data={'email': 'new_cust@example.com', 'user_type': 'customer'}, sociallogin=sl)
        self.assertTrue(form.is_valid(), form.errors)
        rf = RequestFactory()
        req = rf.post('/accounts/social/signup/')
        req.session = {}
        user = form.save(req)
        self.assertEqual(user.user_type, 'customer')
        self.assertTrue(user.is_customer_user)
        self.assertFalse(user.is_technician_user)
        user.delete()

    def test_social_signup_form_technician_role(self):
        from accounts.forms import SocialSignupForm
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        from django.test import RequestFactory
        sa = SocialAccount(provider='google', uid='test_tech_uid', extra_data={'email': 'new_tech@example.com', 'name': 'New Tech'})
        sl = SocialLogin(user=User(email='new_tech@example.com', username='new_tech@example.com'), account=sa)
        form = SocialSignupForm(data={'email': 'new_tech@example.com', 'user_type': 'technician'}, sociallogin=sl)
        self.assertTrue(form.is_valid(), form.errors)
        rf = RequestFactory()
        req = rf.post('/accounts/social/signup/')
        req.session = {}
        user = form.save(req)
        self.assertEqual(user.user_type, 'technician')
        self.assertTrue(user.is_technician_user)
        self.assertFalse(user.is_customer_user)
        user.delete()

    def test_social_signup_form_empty_role_rejected(self):
        from accounts.forms import SocialSignupForm
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        sa = SocialAccount(provider='google', uid='test_empty_uid', extra_data={'email': 'empty_role@example.com'})
        sl = SocialLogin(user=User(email='empty_role@example.com', username='empty_role@example.com'), account=sa)
        form = SocialSignupForm(data={'email': 'empty_role@example.com', 'user_type': ''}, sociallogin=sl)
        self.assertFalse(form.is_valid())
        self.assertIn('user_type', form.errors)

    def test_social_signup_form_invalid_role_rejected(self):
        from accounts.forms import SocialSignupForm
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        sa = SocialAccount(provider='google', uid='test_invalid_uid', extra_data={'email': 'invalid_role@example.com'})
        sl = SocialLogin(user=User(email='invalid_role@example.com', username='invalid_role@example.com'), account=sa)
        for invalid_role in ['admin', 'manager', 'superuser', 'staff', 'other']:
            form = SocialSignupForm(data={'email': 'invalid_role@example.com', 'user_type': invalid_role}, sociallogin=sl)
            self.assertFalse(form.is_valid())
            self.assertIn('user_type', form.errors)

    def test_pre_social_login_existing_technician_preserves_role_without_signup(self):
        from accounts.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        from django.test import RequestFactory
        existing_tech = User.objects.create_user(
            username='existing_tech@example.com',
            email='existing_tech@example.com',
            password='password123',
            user_type='technician'
        )
        adapter = CustomSocialAccountAdapter()
        sa = SocialAccount(provider='google', uid='google_tech_uid', extra_data={'email': 'existing_tech@example.com'})
        sl = SocialLogin(user=User(email='existing_tech@example.com'), account=sa)
        rf = RequestFactory()
        req = rf.get('/accounts/google/login/callback/')
        req.user = existing_tech
        req.session = {}

        adapter.pre_social_login(req, sl)
        self.assertTrue(sl.is_existing)
        self.assertEqual(sl.user, existing_tech)
        self.assertEqual(existing_tech.user_type, 'technician')
        self.assertTrue(existing_tech.is_technician_user)

    def test_pre_social_login_existing_customer_preserves_role_without_signup(self):
        from accounts.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        from django.test import RequestFactory
        existing_cust = User.objects.create_user(
            username='existing_cust@example.com',
            email='existing_cust@example.com',
            password='password123',
            user_type='customer'
        )
        adapter = CustomSocialAccountAdapter()
        sa = SocialAccount(provider='google', uid='google_cust_uid', extra_data={'email': 'existing_cust@example.com'})
        sl = SocialLogin(user=User(email='existing_cust@example.com'), account=sa)
        rf = RequestFactory()
        req = rf.get('/accounts/google/login/callback/')
        req.user = existing_cust
        req.session = {}

        adapter.pre_social_login(req, sl)
        self.assertTrue(sl.is_existing)
        self.assertEqual(sl.user, existing_cust)
        self.assertEqual(existing_cust.user_type, 'customer')
        self.assertTrue(existing_cust.is_customer_user)

    def test_adapter_is_auto_signup_allowed_returns_false(self):
        from accounts.adapters import CustomSocialAccountAdapter
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        adapter = CustomSocialAccountAdapter()
        sa = SocialAccount(provider='google', uid='new_uid', extra_data={'email': 'new_auto@example.com'})
        sl = SocialLogin(user=User(email='new_auto@example.com'), account=sa)
        self.assertFalse(adapter.is_auto_signup_allowed(None, sl))

    def test_social_signup_template_renders_role_options(self):
        from django.template.loader import render_to_string
        from accounts.forms import SocialSignupForm
        from allauth.socialaccount.models import SocialLogin, SocialAccount
        sa = SocialAccount(provider='google', uid='template_test_uid', extra_data={'email': 'template_test@example.com'})
        sl = SocialLogin(user=User(email='template_test@example.com', username='template_test@example.com'), account=sa)
        form = SocialSignupForm(sociallogin=sl)
        rendered = render_to_string('socialaccount/signup.html', {'form': form, 'account': sa})
        self.assertIn('Complete Your Signup', rendered)
        self.assertIn('Customer', rendered)
        self.assertIn('Technician', rendered)
        self.assertIn('value="customer"', rendered)
        self.assertIn('value="technician"', rendered)







