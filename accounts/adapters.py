from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for GearGuard.
    Ensures that any new user signing up via Google OAuth is strictly assigned
    the 'customer' application role, while preserving existing user roles
    (e.g., Technician) if an existing user links/authenticates via Google.
    """

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


        # For newly created users (no DB primary key yet), default role strictly to 'customer'
        if not user.pk:
            user.user_type = 'customer'

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Ensure user_type is never empty or None for new social users
        if not user.user_type:
            user.user_type = 'customer'
            user.save(update_fields=['user_type'])
        return user
