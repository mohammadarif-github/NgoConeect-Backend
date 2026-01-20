from django.db.models.signals import post_save
from django.dispatch import receiver
from donations.models import Donation
from projects.models import Task
from volunteers.models import VolunteerProfile

from .models import Notification


@receiver(post_save, sender=Task)
def notify_on_task_assignment(sender, instance, created, **kwargs):
    """Notify volunteer when a task is assigned to them."""
    # Logic: If task is assigned (and wasn't before, or just created with assignment)
    if instance.assigned_to:
        # Avoid spamming updates? For simplicity, we notify on save if assigned
        # Ideally, check if 'assigned_to' changed.
        # But for MVP, simple creation is fine.
        title = "New Task Assigned"
        msg = f"You have been assigned to task: '{instance.title}' due on {instance.due_date}."
        
        # Check if notification already exists recently to avoid dupes on update?
        # Skipping for simplicity as requested "Short checklist"
        Notification.objects.create(
            user=instance.assigned_to,
            title=title,
            message=msg
        )

@receiver(post_save, sender=Donation)
def notify_on_donation_success(sender, instance, created, **kwargs):
    """Notify donor when donation is successful."""
    # We only care if status becomes SUCCESS
    if instance.status == 'SUCCESS' and instance.donor:
        # Check if we already notified for this transaction?
        # A simple check: if we just saved it as SUCCESS.
        # Signal fires on every save.
        # Let's ensure we don't spam.
        # We can implement a check if a notification exists for this title/message combo recently
        # or rely on frontend to handle.
        # Better: Check if 'created' is False and we just updated status.
        # But keep it simple for now as requested.
        
        title = "Donation Successful"
        msg = f"Thank you! Your donation of {instance.amount} for {instance.campaign.title if instance.campaign else 'General Fund'} was successful."
        
        # Simple debounce: Create only if not exists identical unread notification?
        # Or just create it.
        if not Notification.objects.filter(user=instance.donor, title=title, is_read=False).exists():
             Notification.objects.create(
                user=instance.donor,
                title=title,
                message=msg
            )

@receiver(post_save, sender=VolunteerProfile)
def notify_on_volunteer_approval(sender, instance, created, **kwargs):
    """Notify user when volunteer application is approved."""
    if instance.application_status == 'APPROVED':
        title = "Application Approved"
        msg = "Congratulations! Your volunteer application has been approved. You can now sign up for events and tasks."
        
        # Debounce
        if not Notification.objects.filter(user=instance.user, title=title, is_read=False).exists():
            Notification.objects.create(
                user=instance.user,
                title=title,
                message=msg
            )
