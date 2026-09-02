from django.contrib import admin
from .models import MaintenanceTeam, MaintenanceRequest, MaintenanceHistory

@admin.register(MaintenanceTeam)
class MaintenanceTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'leader', 'created_at']
    filter_horizontal = ['members']
    search_fields = ['name', 'description']

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'equipment', 'status', 'priority', 'assigned_team', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(MaintenanceHistory)
class MaintenanceHistoryAdmin(admin.ModelAdmin):
    list_display = ['maintenance_request', 'performed_by', 'cost', 'created_at']
    list_filter = ['created_at']
    search_fields = ['notes', 'parts_used']
    readonly_fields = ['created_at']
