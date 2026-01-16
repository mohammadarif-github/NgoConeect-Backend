from django.db import models
from user.models import User


class Donation(models.Model):
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
    )

    campaign = models.ForeignKey('projects.Campaign', on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='donations')
    
    donor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='made_donations')
    
    donor_name = models.CharField(max_length=255, blank=True)
    donor_email = models.EmailField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    transaction_id = models.CharField(max_length=255, unique=True, db_index=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    payment_gateway_response = models.JSONField(default=dict, blank=True)
    
    receipt_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Donation Transaction"
        verbose_name_plural = "Donation Transactions"
        indexes = [
            models.Index(fields=['status', 'timestamp']),
            models.Index(fields=['campaign', 'status']),
        ]

    def __str__(self):
        return f"Donation of {self.amount} ({self.status})"

