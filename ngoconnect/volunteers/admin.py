from django.contrib import admin

from .models import TimeLog, VolunteerProfile


class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'application_status', 'availability')
    list_filter = ('application_status',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'skills')

class TimeLogAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'task', 'start_time', 'end_time', 'duration_minutes')
    list_filter = ('volunteer', 'task', 'start_time')
    search_fields = ('volunteer__email', 'task__title')

admin.site.register(VolunteerProfile, VolunteerProfileAdmin)
admin.site.register(TimeLog, TimeLogAdmin)

