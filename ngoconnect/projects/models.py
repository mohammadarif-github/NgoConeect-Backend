from decimal import Decimal

from django.db import models
from user.models import User


# --- Campaign Model (The 'Project') ---
class Campaign(models.Model):
    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField()
    
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    budget_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    
    # Only Admin or Manager can create campaigns
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role__in': ['admin', 'manager']}, 
                                 related_name='created_campaigns')

    class Meta:
        verbose_name = "Campaign/Project"
        verbose_name_plural = "Campaigns/Projects"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'end_date']),
        ]

    def __str__(self):
        return self.title

# --- Task Model ---
class Task(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Task assigned only to a Volunteer
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    limit_choices_to={'role': 'volunteer'}, 
                                    related_name='assigned_tasks')
    
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Project Task"
        verbose_name_plural = "Project Tasks"
        # Composite index for quickly listing a volunteer's tasks by due date
        indexes = [
            models.Index(fields=['campaign', 'is_completed']),
            models.Index(fields=['assigned_to', 'due_date']),
        ]

    def __str__(self):
        return f"{self.campaign.title} - {self.title}"
# --- Event Model (New Requirement FR-CAMP-02) ---
class Event(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=255)
    
    capacity = models.PositiveIntegerField(default=0, help_text="Maximum number of volunteers (0 for unlimited)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return f"{self.title} ({self.start_datetime.date()})"
    
    @property
    def participants_count(self):
        return self.participants.count()
    
    @property
    def is_full(self):
        if self.capacity == 0:
            return False
        return self.participants.count() >= self.capacity


class EventParticipant(models.Model):
    STATUS_CHOICES = (
        ('REGISTERED', 'Registered'),
        ('ATTENDED', 'Attended'),
        ('CANCELLED', 'Cancelled'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_signups',
                                  limit_choices_to={'role': 'volunteer'})
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    signup_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('event', 'volunteer')
        ordering = ['-signup_date']

    def __str__(self):
        return f"{self.volunteer.email} - {self.event.title}"
