from django import forms
from allauth.socialaccount.forms import SignupForm
from django.core.exceptions import ValidationError


class SocialSignupForm(SignupForm):
    """
    Form used during new social (Google OAuth) signup to allow the user
    to select their application role: Customer or Technician.
    """
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('technician', 'Technician'),
    )

    user_type = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        error_messages={
            'required': 'Please select your role (Customer or Technician) to continue.',
            'invalid_choice': 'Invalid role selected. Only Customer or Technician can be selected.',
        }
    )

    def clean_user_type(self):
        user_type = self.cleaned_data.get('user_type')
        if user_type not in ('customer', 'technician'):
            raise ValidationError('Invalid role selected. Please choose Customer or Technician.')
        return user_type

    def save(self, request):
        user = super().save(request)
        role = self.cleaned_data.get('user_type')
        if role in ('customer', 'technician'):
            user.user_type = role
            user.save(update_fields=['user_type'])
        return user
