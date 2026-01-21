# volunteer/serializers.py
from rest_framework import serializers

from .models import TimeLog, VolunteerProfile


class VolunteerApplySerializer(serializers.ModelSerializer):
    """For users applying as volunteers."""
    
    class Meta:
        model = VolunteerProfile
        fields = ('skills', 'availability')
    
    def validate(self, attrs):
        user = self.context['request'].user
        
        # Prevent Admin/Managers from applying as volunteers (downgrading role)
        if user.role in ['admin', 'manager']:
            raise serializers.ValidationError("Admins and Managers cannot apply as volunteers.")

        if VolunteerProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError("You have already applied as a volunteer.")
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        # Do NOT update role to 'volunteer' immediately 
        # Wait for Admin approval to change role or handle it logic elsewhere if 'volunteer' role is strictly for approved ones
        # For now, we will NOT change the role here, preventing the hijacking issue.
        # User remains 'general_user' until approved? 
        # Requirement says: "Admin shall review and approve/reject".
        
        return VolunteerProfile.objects.create(user=user, **validated_data)


class VolunteerProfileSerializer(serializers.ModelSerializer):
    """For viewing volunteer profile."""
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = VolunteerProfile
        fields = (
            'email', 'first_name', 'last_name',
            'skills', 'availability', 'application_status'
        )
        read_only_fields = ('application_status',)


class VolunteerUpdateSerializer(serializers.ModelSerializer):
    """For volunteers updating their own profile."""
    
    class Meta:
        model = VolunteerProfile
        fields = ('skills', 'availability')


class VolunteerAdminSerializer(serializers.ModelSerializer):
    """For admin viewing volunteer applications."""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = VolunteerProfile
        fields = (
            'user_id', 'email', 'first_name', 'last_name',
            'skills', 'availability', 'application_status'
        )



class VolunteerReviewSerializer(serializers.Serializer):
    """For admin approving/rejecting volunteers."""
    application_status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])


# --- Time Log Serializers ---
class TimeLogSerializer(serializers.ModelSerializer):
    """For viewing time logs."""
    task_name = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = TimeLog
        fields = ('id', 'task', 'task_name', 'start_time', 'end_time', 'duration_minutes')
        read_only_fields = ('id', 'duration_minutes')


class TimeLogCreateSerializer(serializers.ModelSerializer):
    """For volunteers logging time."""
    
    class Meta:
        model = TimeLog
        fields = ('task', 'start_time', 'end_time')
    
    def validate(self, attrs):
        if attrs['end_time'] <= attrs['start_time']:
            raise serializers.ValidationError("End time must be after start time.")
        return attrs
    
    def create(self, validated_data):
        validated_data['volunteer'] = self.context['request'].user
        return super().create(validated_data)
    
class VolunteerAdminDetailSerializer(VolunteerAdminSerializer):
    """For admin viewing detailed volunteer profile including logs and tasks."""
    time_logs = TimeLogSerializer(source='user.time_logs', many=True, read_only=True)
    assigned_tasks = serializers.SerializerMethodField()

    class Meta(VolunteerAdminSerializer.Meta):
        fields = VolunteerAdminSerializer.Meta.fields + ('time_logs', 'assigned_tasks')

    def get_assigned_tasks(self, obj):
        tasks = obj.user.assigned_tasks.all()
        return [
            {
                'id': t.id,
                'title': t.title,
                'campaign': t.campaign.title,
                'due_date': t.due_date,
                'is_completed': t.is_completed
            }
            for t in tasks
        ]