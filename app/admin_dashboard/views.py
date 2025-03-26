from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

from authentication.models import CustomUser
from authentication.serializers import UserSerializer
from utils import api_response

@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_list(request):
    users = CustomUser.objects.all()
    serializer = UserSerializer(users, many=True)
    return api_response(status.HTTP_200_OK, "List of all users", serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def inactive_users(request):
    five_months_ago = now() - relativedelta(months=5)
    inactive_users = CustomUser.objects.filter(last_login__lt=five_months_ago)
    serializer = UserSerializer(inactive_users, many=True)
    return api_response(status.HTTP_200_OK, "Users inactive for more than 5 months", serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    if not isinstance(user_id, int):
        return api_response(status.HTTP_400_BAD_REQUEST, "Invalid user ID format")
    
    try:
        user = CustomUser.objects.get(id=user_id)
        if user.is_superuser or user.is_staff:
            return api_response(status.HTTP_403_FORBIDDEN, "Cannot delete admin or superuser")
        
        user.delete()
        return api_response(status.HTTP_200_OK, "User successfully deleted")
    except CustomUser.DoesNotExist:
        return api_response(status.HTTP_404_NOT_FOUND, "User not found")
