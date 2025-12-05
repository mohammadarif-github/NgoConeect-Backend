from django.db import models
from datetime import timedelta
from user.models import User


# --- Volunteer Profile Model ---
class VolunteerProfile(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, 
                                limit_choices_to={'role': 'volunteer'})
    skills = models.TextField(blank=True, help_text="List skills, e.g., 'Python, Marketing, Design'")
    availability = models.CharField(max_length=100, blank=True)
    application_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    class Meta:
        verbose_name = "Volunteer Profile"
        verbose_name_plural = "Volunteer Profiles"
        indexes = [
            models.Index(fields=['application_status']),
        ]

    def __str__(self):
        return f"Profile for {self.user.get_full_name() or self.user.email}"

# --- Time Log Model ---
class TimeLog(models.Model):
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, 
                                  limit_choices_to={'role': 'volunteer'}, related_name='time_logs')
    task = models.ForeignKey('projects.Task', on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='time_logs')
                             
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField(editable=False, null=True, 
                                           help_text="Calculated duration in minutes.")

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            duration: timedelta = self.end_time - self.start_time
            self.duration_minutes = int(duration.total_seconds() / 60)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Volunteer Time Log"
        verbose_name_plural = "Volunteer Time Logs"
        indexes = [
            models.Index(fields=['volunteer', 'start_time']),
        ]

    def __str__(self):
        return f"{self.volunteer.email} - {self.duration_minutes} minutes"
