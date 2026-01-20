from django.contrib import admin

from .models import Campaign, Event, Task


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'goal_amount', 'budget_allocated', 'start_date', 'end_date', 'created_by')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'campaign', 'assigned_to', 'due_date', 'is_completed')
    list_filter = ('is_completed', 'due_date', 'campaign')
    search_fields = ('title', 'description', 'campaign__title')
    list_editable = ('is_completed',)
    
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'campaign', 'start_datetime', 'end_datetime')
    list_filter = ('start_datetime', 'end_datetime', 'campaign')
    search_fields = ('title', 'description', 'campaign__title')

admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Event, EventAdmin)