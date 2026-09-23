from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    USER_TYPES = (
        ('technician', 'Technician'),
        ('customer', 'Customer'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='customer'
    )

    mobile_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    @property
    def is_admin_user(self):
        return self.is_staff or self.is_superuser or self.user_type in ['admin', 'manager', 'technician']

    @property
    def is_technician_user(self):
        return self.user_type == 'technician'

    @property
    def is_customer_user(self):
        return self.user_type == 'customer'

    @property
    def is_team_leader(self):
        return self.led_teams.exists()

    @property
    def can_manage_equipment(self):
        return self.is_staff or self.is_superuser or self.user_type in ['admin', 'manager', 'technician']

    @property
    def can_assign_requests(self):
        return self.is_staff or self.is_superuser or self.user_type in ['admin', 'manager', 'technician'] or self.is_team_leader

    def can_edit_request(self, request_obj):
        if self.is_admin_user:
            return True
        if request_obj.requested_by == self:
            return True
        if request_obj.assigned_technician == self:
            return True
        if request_obj.assigned_team:
            if request_obj.assigned_team.leader == self:
                return True
            if self in request_obj.assigned_team.members.all():
                return True
        return False