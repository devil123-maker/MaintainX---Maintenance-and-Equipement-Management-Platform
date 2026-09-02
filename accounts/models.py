from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    USER_TYPES = (
        ('technician', 'Technician'),
        ('customer', 'Customer'),
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES
    )

    mobile_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )