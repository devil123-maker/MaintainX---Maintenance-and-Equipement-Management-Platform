from django.contrib import admin
from .models import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'serial_number', 'status', 'location', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'serial_number', 'model', 'manufacturer']
    readonly_fields = ['created_at', 'updated_at']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return list(self.readonly_fields) + ['created_by']
        return self.readonly_fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj is None:
            return [f for f in fields if f != 'created_by']
        return fields

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
