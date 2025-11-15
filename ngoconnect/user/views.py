from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import User
from .serializers import UserSerializer


class UserListAPIView(APIView):
    """API view to fetch all users."""
    
    permission_classes = [AllowAny]  
    
    def get(self, request):
        """Get all users."""
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response({
            'success': True,
            'count': users.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
