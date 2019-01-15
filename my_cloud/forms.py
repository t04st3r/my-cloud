from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError


# TODO create an app for authentication purposes and move this form there
class EmailAuthenticationForm(AuthenticationForm):
    """ Perform login using either username or email address """
    def clean_username(self):
        username = self.data['username']
        if '@' in username:
            try:
                username = User.objects.get(email=username).username
            except ObjectDoesNotExist:
                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid login',
                    params={'username': self.username_field.verbose_name},
                )
        return username
