from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # First try the standard Authorization header
        result = super().authenticate(request)
        if result is not None:
            return result

        # Fall back to access_token cookie
        access_token = request.COOKIES.get('access_token')
        if access_token:
            try:
                validated_token = self.get_validated_token(access_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except Exception:
                return None

        return None
