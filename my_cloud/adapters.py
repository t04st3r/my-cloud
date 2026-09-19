from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    """Close local (password) self-registration."""

    def is_open_for_signup(self, request):
        return False


class GoogleSignupAdapter(DefaultSocialAccountAdapter):
    """Keep social (Google) signup open.

    ``DefaultSocialAccountAdapter.is_open_for_signup`` delegates to the account
    adapter, which we closed above; override it so new users can still be
    created by signing in with Google.
    """

    def is_open_for_signup(self, request, sociallogin):
        return True
