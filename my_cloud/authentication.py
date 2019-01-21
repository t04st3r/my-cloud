from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CustomAuthentication(ModelBackend):
    """
    Authenticate users both using email address or username
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        try:
            if '@' in username:
                user = user_model.objects.get(email=username)
            else:
                user = user_model.objects.get(username=username)
        except user_model.DoesNotExist:
            return None
        else:
            if self.user_can_authenticate(user) and user.check_password(password):
                return user
        return None
