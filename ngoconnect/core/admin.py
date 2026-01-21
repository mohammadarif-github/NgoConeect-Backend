from django.contrib import admin

from .models import ContactMessage


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'timestamp', 'is_resolved')
    list_filter = ('is_resolved', 'timestamp')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('timestamp',)

admin.site.register(ContactMessage, ContactMessageAdmin)