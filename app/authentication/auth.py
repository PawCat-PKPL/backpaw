from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom authentication class that uses JWT tokens stored in cookies.
    """

    def authenticate(self, request):
        """
        Authenticate the user based on the JWT token in the cookie.
        """
        # Extract the JWT token from the cookie
        token = request.COOKIES.get('access_token')
        if not token:
            return None

        # Decode the JWT token and extract user information
        try:
            print("=== Token dari Cookie ===")
            print(token)

            validated_token = self.get_validated_token(token)

        except AuthenticationFailed as e:
            raise AuthenticationFailed(f'Token validation failed: {str(e)}')
        
        try:
            user = self.get_user(validated_token)
            return user, validated_token
        except AuthenticationFailed as e:
            raise AuthenticationFailed(f'Error retrieving user: {str(e)}')