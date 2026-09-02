from django.urls import path
from .views import equipment_list, equipment_detail

urlpatterns = [
    path('equipment/', equipment_list, name='equipment_list'),
    path('equipment/<int:pk>/', equipment_detail, name='equipment_detail'),
]
