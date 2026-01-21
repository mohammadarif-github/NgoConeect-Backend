from django.contrib import admin

from .models import Donation


class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor_name', 'donor_email', 'amount', 'status', 'transaction_id', 'campaign', 'timestamp')
    list_filter = ('status', 'timestamp', 'campaign')
    search_fields = ('donor_name', 'donor_email', 'transaction_id')
    readonly_fields = ('transaction_id', 'payment_gateway_response', 'timestamp', 'updated_at')

admin.site.register(Donation, DonationAdmin)
