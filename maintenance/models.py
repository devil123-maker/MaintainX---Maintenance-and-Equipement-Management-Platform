from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class MaintenanceTeam(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='led_teams'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class MaintenanceRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('repaired', 'Repaired'),
        ('scrap', 'Scrap'),
        ('cancelled', 'Cancelled'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    REQUEST_TYPE_CHOICES = (
        ('corrective', 'Corrective'),
        ('preventive', 'Preventive'),
    )

    DURATION_UNIT_CHOICES = (
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.CASCADE,
        related_name='maintenance_requests'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_maintenances'
    )
    assigned_team = models.ForeignKey(
        MaintenanceTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests'
    )
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_maintenance_requests'
    )
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='corrective'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    scheduled_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    duration_value = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )
    duration_unit = models.CharField(
        max_length=10,
        choices=DURATION_UNIT_CHOICES,
        default='minutes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"

    @property
    def duration_display(self):
        from decimal import Decimal
        if self.duration_value is not None:
            val = self.duration_value
            formatted_val = f"{val:.2f}".rstrip('0').rstrip('.') if isinstance(val, (float, Decimal)) else str(val)
            if self.duration_unit == 'minutes':
                return f"{formatted_val} mins"
            elif self.duration_unit == 'hours':
                return f"{formatted_val} hrs"
            elif self.duration_unit == 'days':
                return f"{formatted_val} {'day' if val == 1 else 'days'}"
            return f"{formatted_val} {self.duration_unit}"
        elif self.duration_hours is not None:
            val = self.duration_hours
            if val < 1:
                return f"{int(round(val * 60))} mins"
            formatted_val = f"{val:.2f}".rstrip('0').rstrip('.')
            return f"{formatted_val} hrs"
        return ""

    @property
    def is_overdue(self):
        if not self.scheduled_date:
            return False
        if self.status in ['completed', 'repaired', 'scrap', 'cancelled']:
            return False
        return self.scheduled_date < timezone.now().date()

    def clean(self):
        super().clean()
        
        # 1. Scrapped Equipment Protection
        if self.equipment_id and self.equipment.status == 'scrapped':
            if not self.pk:
                raise ValidationError({'equipment': 'Cannot create a new maintenance request for scrapped equipment.'})
            else:
                orig = MaintenanceRequest.objects.filter(pk=self.pk).first()
                if orig and orig.equipment_id != self.equipment_id:
                    raise ValidationError({'equipment': 'Cannot assign scrapped equipment to a maintenance request.'})

        # 2. Auto-fill Maintenance Team from Equipment if omitted
        if self.equipment_id:
            if not self.assigned_team_id and self.equipment.maintenance_team_id:
                self.assigned_team = self.equipment.maintenance_team

        # 3. Validate Equipment-Team Consistency
        if self.equipment_id and self.equipment.maintenance_team_id and self.assigned_team_id:
            if self.assigned_team_id != self.equipment.maintenance_team_id:
                raise ValidationError({'assigned_team': 'Assigned team must match the equipment\'s maintenance team.'})

        # 4. Validate Technician belongs to Assigned Maintenance Team
        if self.assigned_technician_id and self.assigned_team_id:
            is_member = self.assigned_team.members.filter(pk=self.assigned_technician_id).exists()
            is_leader = self.assigned_team.leader_id == self.assigned_technician_id
            if not (is_member or is_leader):
                raise ValidationError({'assigned_technician': 'Selected technician does not belong to the assigned maintenance team.'})

        # 5. Status Transition Rules Validation
        if self.pk:
            orig = MaintenanceRequest.objects.filter(pk=self.pk).first()
            if orig and orig.status != self.status:
                terminal_statuses = ['completed', 'repaired', 'scrap', 'cancelled']
                if orig.status in terminal_statuses:
                    raise ValidationError({'status': f'Cannot transition status from terminal state \'{orig.status}\' to \'{self.status}\'.'})
                # Disallow direct jump from new/pending to repaired/completed
                if orig.status in ['new', 'pending'] and self.status in ['repaired', 'completed']:
                    raise ValidationError({'status': f'Cannot transition directly from \'{orig.status}\' to \'{self.status}\'. Ticket must be in progress first.'})

        # 6. Validate that In Progress requires an assigned technician
        if self.status == 'in_progress' and not self.assigned_technician_id:
            raise ValidationError({'assigned_technician': 'Cannot move request to In Progress without an assigned technician.'})

        # 7. Sync duration_value and duration_unit with duration_hours
        from decimal import Decimal
        if self.duration_value is not None:
            val = float(self.duration_value)
            if self.duration_unit == 'minutes':
                self.duration_hours = Decimal(str(round(val / 60.0, 2)))
            elif self.duration_unit == 'hours':
                self.duration_hours = Decimal(str(round(val, 2)))
            elif self.duration_unit == 'days':
                self.duration_hours = Decimal(str(round(val * 24.0, 2)))
        elif self.duration_hours is not None and self.duration_value is None:
            self.duration_value = self.duration_hours
            self.duration_unit = 'hours'

    def can_technician_join(self, user):
        """Reusable check: Can this technician see and join this maintenance request?"""
        if not user or not user.is_authenticated:
            return False
        if not getattr(user, 'is_technician_user', False):
            return False
        if self.status not in ['new', 'pending']:
            return False
        if self.assigned_technician_id is not None:
            return False
        if not self.assigned_team_id:
            return False
        if self.equipment_id and self.equipment.status == 'scrapped':
            return False
        return self.assigned_team.members.filter(pk=user.pk).exists() or self.assigned_team.leader_id == user.pk

    def is_assigned_to(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.assigned_technician_id == user.pk

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Check if transitioning to 'scrap' status
        is_scrapping = False
        if self.status == 'scrap':
            if not self.pk:
                is_scrapping = True
            else:
                orig = MaintenanceRequest.objects.filter(pk=self.pk).first()
                if orig and orig.status != 'scrap':
                    is_scrapping = True

        if is_scrapping and self.equipment_id:
            with transaction.atomic():
                super().save(*args, **kwargs)
                self.equipment.status = 'scrapped'
                self.equipment.save()
        else:
            super().save(*args, **kwargs)


class MaintenanceHistory(models.Model):
    maintenance_request = models.ForeignKey(
        MaintenanceRequest,
        on_delete=models.CASCADE,
        related_name='history'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    parts_used = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"History for {self.maintenance_request.title}"
