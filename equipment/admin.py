from django.contrib import admin
from .models import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'serial_number', 'status', 'location', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'serial_number', 'model', 'manufacturer']
    readonly_fields = ['created_at', 'updated_at']
