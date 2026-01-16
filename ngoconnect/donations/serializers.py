from projects.models import Campaign
from rest_framework import serializers

from .models import Donation


class DonationInitiateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=10.0)
    campaign_id = serializers.IntegerField(required=False, allow_null=True)
    
    # Guest details (optional if logged in, required if guest)
    guest_name = serializers.CharField(required=False, allow_blank=True)
    guest_email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            if not attrs.get('guest_email') or not attrs.get('guest_name'):
                raise serializers.ValidationError("Guest name and email are required for non-logged-in users.")
        return attrs

class DonationAdminSerializer(serializers.ModelSerializer):
    campaign_title = serializers.ReadOnlyField(source='campaign.title')
    donor_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Donation
        fields = '__all__'
        
    def get_donor_info(self, obj):
        if obj.donor:
            return f"{obj.donor.first_name} {obj.donor.last_name} ({obj.donor.email})"
        return f"{obj.donor_name} ({obj.donor_email})"

class DonationPublicSerializer(serializers.ModelSerializer):
    donor_name_display = serializers.SerializerMethodField()
    campaign_title = serializers.ReadOnlyField(source='campaign.title')
    
    class Meta:
        model = Donation
        fields = ('id', 'donor_name_display', 'amount', 'timestamp', 'campaign_title')
        
    def get_donor_name_display(self, obj):
        # Privacy: obscure name slightly or just first name
        name = obj.donor.first_name if obj.donor else obj.donor_name
        if not name:
            return "Anonymous"
        parts = name.split()
        if len(parts) > 1:
            return f"{parts[0]} {parts[-1][0]}."
        return name
