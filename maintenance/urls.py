from django.urls import path
from .views import (
    team_list, team_detail, team_add_member, team_remove_member,
    request_list, request_detail, request_assign_team, request_complete, request_join,
    history_list, history_detail, dashboard,
    tickets_view, create_ticket_view, workers_view, analytics_view, settings_view,
    calendar_view
)

urlpatterns = [
    # Teams
    path('teams/', team_list, name='team_list'),
    path('teams/<int:pk>/', team_detail, name='team_detail'),
    path('teams/<int:pk>/add_member/', team_add_member, name='team_add_member'),
    path('teams/<int:pk>/remove_member/', team_remove_member, name='team_remove_member'),
    
    # Requests
    path('requests/', request_list, name='request_list'),
    path('requests/<int:pk>/', request_detail, name='request_detail'),
    path('requests/<int:pk>/join/', request_join, name='request_join'),
    path('requests/<int:pk>/assign_team/', request_assign_team, name='request_assign_team'),
    path('requests/<int:pk>/complete/', request_complete, name='request_complete'),
    
    # History
    path('history/', history_list, name='history_list'),
    path('history/<int:pk>/', history_detail, name='history_detail'),
    
    # Dashboard & Pages
    path('dashboard/', dashboard, name='dashboard'),
    path('tickets/', tickets_view, name='tickets'),
    path('calendar/', calendar_view, name='calendar'),
    path('create-ticket/', create_ticket_view, name='create_ticket'),
    path('workers/', workers_view, name='workers'),
    path('analytics/', analytics_view, name='analytics'),
    path('settings/', settings_view, name='settings'),
]

