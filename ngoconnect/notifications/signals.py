from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from donations.models import Donation
from projects.models import Task
from volunteers.models import VolunteerProfile

from .models import Notification

# --- 1. Track Changes via Pre-Save ---

@receiver(pre_save, sender=Task)
def task_pre_save_handler(sender, instance, **kwargs):
    """Track previous assigned_to value."""
    if instance.pk:
        try:
            old_task = Task.objects.get(pk=instance.pk)
            instance._old_assigned_to = old_task.assigned_to
        except Task.DoesNotExist:
            instance._old_assigned_to = None
    else:
        instance._old_assigned_to = None

@receiver(pre_save, sender=VolunteerProfile)
def volunteer_pre_save_handler(sender, instance, **kwargs):
    """Track previous application_status."""
    if instance.pk: # VolunteerProfile pk is user_id, which always exists on update
        try:
            old_profile = VolunteerProfile.objects.get(pk=instance.pk)
            instance._old_status = old_profile.application_status
        except VolunteerProfile.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(pre_save, sender=Donation)
def donation_pre_save_handler(sender, instance, **kwargs):
    """Track previous status."""
    if instance.pk:
        try:
            old_donation = Donation.objects.get(pk=instance.pk)
            instance._old_status = old_donation.status
        except Donation.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# --- 2. Create Notifications on Post-Save ---

@receiver(post_save, sender=Task)
def notify_on_task_assignment(sender, instance, created, **kwargs):
    """Notify volunteer when a task is assigned to them."""
    
    should_notify = False
    
    # Logic: Notify if (1) newly created with assignment OR (2) updated and assignment changed to a user
    if created and instance.assigned_to:
        should_notify = True
    elif not created and instance.assigned_to:
        # Check if it changed
        old_assigned = getattr(instance, '_old_assigned_to', None)
        if old_assigned != instance.assigned_to:
            should_notify = True
    
    if should_notify:
        title = "New Task Assigned"
        msg = f"You have been assigned to task: '{instance.title}' due on {instance.due_date}."
        
        Notification.objects.create(
            user=instance.assigned_to,
            title=title,
            message=msg
        )

@receiver(post_save, sender=Donation)
def notify_on_donation_success(sender, instance, created, **kwargs):
    """Notify donor when donation is successful."""
    
    should_notify = False
    
    # Logic: Notify if status CHANGED to SUCCESS
    # Note: Donations usually start as PENDING, so creation with SUCCESS is rare but possible manually.
    
    if instance.status == 'SUCCESS' and instance.donor:
        if created:
            should_notify = True
        else:
            old_status = getattr(instance, '_old_status', None)
            if old_status != 'SUCCESS': # Status changed TO Success
                should_notify = True

    if should_notify:
        title = "Donation Successful"
        msg = f"Thank you! Your donation of {instance.amount} for {instance.campaign.title if instance.campaign else 'General Fund'} was successful."
        
        Notification.objects.create(
            user=instance.donor,
            title=title,
            message=msg
        )

@receiver(post_save, sender=VolunteerProfile)
def notify_on_volunteer_approval(sender, instance, created, **kwargs):
    """Notify user when volunteer application is approved."""
    
    should_notify = False
    
    if instance.application_status == 'APPROVED':
        # Logic: Notify if status CHANGED to APPROVED
        if created: # Creating a profile directly as APPROVED
            should_notify = True
        else:
            old_status = getattr(instance, '_old_status', None)
            if old_status != 'APPROVED':
                should_notify = True
            
    if should_notify:
        title = "Application Approved"
        msg = "Congratulations! Your volunteer application has been approved. You can now sign up for events and tasks."
        
        Notification.objects.create(
            user=instance.user,
            title=title,
            message=msg
        )
