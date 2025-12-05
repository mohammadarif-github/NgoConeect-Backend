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
    budget_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
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