# yourapp/forms.py
from allauth.account.forms import LoginForm
from django import forms
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

class CustomLoginForm(LoginForm):
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': _('Password')}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")

        print(f"Cleaned password: {password}")

        try:
            validate_password(password)
        except ValidationError as e:
            print(f"Validation error: {e}")

        return cleaned_data

# class CustomSignupForm(SignupForm):
#     password = forms.CharField(
#         label=_("Password"),
#         widget=forms.PasswordInput(attrs={'placeholder': _('Password')}),
#         strip=False,
#     )

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Exclude the password2 field
#         self.fields.pop('password1', None)

#     def clean(self):
#         cleaned_data = super().clean()
#         password = cleaned_data.get("password")

#         try:
#             validate_password(password)
#         except ValidationError as e:
#             for error in e.error_list:
#                 if "too common" in str(error):
#                     self.add_error("password", _("Ο κωδικός πρόσβασης είναι πολύ συνηθισμένος."))
#                 elif "at least" in str(error):
#                     # Customize error message for the minimum length requirement
#                     self.add_error("password", _("Ο κωδικός πρόσβασης πρέπει να περιέχει τουλάχιστον 8 χαρακτήρες."))
#                 elif "numeric" in str(error):
#                     # Customize error message for the minimum length requirement
#                     self.add_error("password", _("Ο κωδικός πρόσβασης δεν μπορεί να περιέχει μόνο αριθμούς."))
#                 elif "personal information" in str(error):
#                     # Customize error message for the minimum length requirement
#                     self.add_error("password", _("Ο κωδικός πρόσβασης δεν μπορεί να έχει μεγάλη ομοιότητα με άλλες προσωπικές πληροφορίες."))


#         return cleaned_data

