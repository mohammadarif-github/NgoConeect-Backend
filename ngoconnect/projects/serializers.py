# projects/serializers.py
from django.utils.text import slugify
from rest_framework import serializers

from .models import Campaign, Event, EventParticipant, Task


class CampaignSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.first_name')
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ('slug', 'created_by', 'budget_allocated', 'current_amount')

    def get_progress_percentage(self, obj):
        if obj.goal_amount > 0:
            percent = (obj.current_amount / obj.goal_amount) * 100
            return round(percent, 2)
        return 0.0

    def create(self, validated_data):
        # Auto-generate unique slug
        if 'slug' not in validated_data:
            base_slug = slugify(validated_data.get('title', ''))
            slug = base_slug
            counter = 1
            while Campaign.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            validated_data['slug'] = slug
        return super().create(validated_data)

    def validate(self, attrs):
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['end_date'] < attrs['start_date']:
                raise serializers.ValidationError({"end_date": ["End date cannot be before start date."]})
        return attrs

class TaskSerializer(serializers.ModelSerializer):
    campaign_title = serializers.ReadOnlyField(source='campaign.title')
    assigned_to_name = serializers.ReadOnlyField(source='assigned_to.first_name')
    
    class Meta:
        model = Task
        fields = '__all__'
        
    def validate_assigned_to(self, value):
        if value and value.role != 'volunteer':
            raise serializers.ValidationError("Task must be assigned to a user with 'volunteer' role.")
        return value

class EventSerializer(serializers.ModelSerializer):
    campaign_title = serializers.ReadOnlyField(source='campaign.title')
    participants_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('created_at',)

    def get_is_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'volunteer':
            return EventParticipant.objects.filter(event=obj, volunteer=request.user).exists()
        return False

class EventParticipantSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.ReadOnlyField(source='volunteer.first_name')
    volunteer_email = serializers.ReadOnlyField(source='volunteer.email')
    event_title = serializers.ReadOnlyField(source='event.title')
    
    class Meta:
        model = EventParticipant
        fields = '__all__'
        read_only_fields = ('signup_date', 'status')
