from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for GearGuard.
    - If an existing user (Customer or Technician) logs in via Google with a matching email,
      they are linked and logged in immediately, preserving their existing role with NO role selection.
    - If this is a new Google signup, the user goes through role selection (SocialSignupForm)
      to choose Customer or Technician, and the selected role is assigned on creation.
    """

    def pre_social_login(self, request, sociallogin):
        # If the social account is already linked to an existing user, is_existing is True
        if sociallogin.is_existing:
            return

        # Check if an existing local user has the same email from Google
        email = None
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
        elif hasattr(sociallogin, 'account') and sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email')

        if email:
            try:
                existing_user = User.objects.get(email__iexact=email)
                # Connect this socialaccount to the existing user so they log in immediately without role selection
                sociallogin.connect(request, existing_user)
            except User.DoesNotExist:
                pass

    def is_auto_signup_allowed(self, request, sociallogin):
        # Return False for new social accounts so the user goes through the role selection signup form
        return False

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Ensure email is populated from social account data
        email = data.get('email')
        if not email and hasattr(sociallogin, 'account') and sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email')
        if email and not user.email:
            user.email = email

        # Ensure username is populated (AbstractUser requires username)
        if not user.username:
            user.username = user.email or data.get('username') or ''

        # Ensure full name is captured into first_name if available
        name = data.get('name')
        if not name and hasattr(sociallogin, 'account') and sociallogin.account.extra_data:
            name = sociallogin.account.extra_data.get('name')
        if name:
            user.first_name = name

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if form and hasattr(form, 'cleaned_data') and 'user_type' in form.cleaned_data:
            role = form.cleaned_data['user_type']
            if role in ('customer', 'technician'):
                user.user_type = role
                user.save(update_fields=['user_type'])
        elif not user.user_type:
            user.user_type = 'customer'
            user.save(update_fields=['user_type'])
        return user
