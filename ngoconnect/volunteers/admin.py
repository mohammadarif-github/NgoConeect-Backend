from django.contrib import admin

from .models import TimeLog, VolunteerProfile

admin.site.register(VolunteerProfile)
admin.site.register(TimeLog)

