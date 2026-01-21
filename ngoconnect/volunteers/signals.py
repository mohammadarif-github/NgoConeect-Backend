from django.db.models.signals import post_save
from django.dispatch import receiver
from user.models import User

from .models import VolunteerProfile


@receiver(post_save, sender=User)
def sync_volunteer_profile_status(sender, instance, created, **kwargs):
    """
    If a User's role is set to 'volunteer' (e.g. via Admin Panel),
    automatically auto-approve their pending volunteer profile.
    """
    if instance.role == 'volunteer':
        try:
            profile = VolunteerProfile.objects.get(user=instance)
            if profile.application_status != 'APPROVED':
                profile.application_status = 'APPROVED'
                # Disable signals temporarily to avoid recursion if needed? 
                # Actually, simply checking the value prevents infinite loops.
                profile.save()
        except VolunteerProfile.DoesNotExist:
            pass

@receiver(post_save, sender=VolunteerProfile)
def sync_user_role(sender, instance, created, **kwargs):
    """
    If a VolunteerProfile is APPROVED (e.g. via Admin Panel),
    automatically update the User's role to 'volunteer'.
    """
    if instance.application_status == 'APPROVED':
        user = instance.user
        # Don't downgrade Admins/Managers to Volunteers automatically
        if user.role not in ['admin', 'manager', 'volunteer']:
            user.role = 'volunteer'
            user.save()
