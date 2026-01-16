# projects/urls.py
from django.urls import path

from . import views

urlpatterns = [
    # Campaign URLs
    path('campaigns/', views.CampaignListCreateView.as_view(), name='campaign-list'),
    path('campaigns/<slug:slug>/', views.CampaignDetailView.as_view(), name='campaign-detail'),

    # Task URLs
    path('tasks/', views.TaskListCreateView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:pk>/complete/', views.MarkTaskCompleteView.as_view(), name='task-mark-complete'),

    # Event URLs (FR-CAMP-02)
    path('events/', views.EventListCreateView.as_view(), name='event-list'),
    path('events/<int:pk>/signup/', views.EventSignupView.as_view(), name='event-signup'),
]