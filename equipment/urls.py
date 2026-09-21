from django.urls import path
from .views import equipment_list, equipment_detail, equipment_maintenance

urlpatterns = [
    path('equipment/', equipment_list, name='equipment_list'),
    path('equipment/<int:pk>/', equipment_detail, name='equipment_detail'),
    path('equipment/<int:pk>/maintenance/', equipment_maintenance, name='equipment_maintenance'),
]
