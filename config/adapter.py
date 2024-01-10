from allauth.account.adapter import DefaultAccountAdapter
from django.forms import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import validate_password
from django import forms

class RestrictEmailAdapter(DefaultAccountAdapter):

    def clean_email(self,email):
        if not email.endswith('@sch.gr'):
            raise ValidationError('Μπορείτε να κάνετε εγγραφή μόνο με email που ανήκει στο domain sch.gr')
        
        # Check if a user with the given email already exists
        # User = get_user_model()
        # if User.objects.filter(email__iexact=email).exists():
        #     raise forms.ValidationError(_("Υπάρχει ήδη χρήστης με αυτή τη διεύθυνση email."))

        return email

    # def clean_password(self, password, user=None):
    #     try:
    #         validate_password(password, user)
    #     except ValidationError as e:
    #         error_messages = []
    #         for error in e.error_list:
    #             if "too common" in str(error):
    #                 error_messages.append(_("Ο κωδικός πρόσβασης είναι πολύ συνηθισμένος."))
    #             elif "at least" in str(error):
    #                 error_messages.append(_("Ο κωδικός πρόσβασης πρέπει να περιέχει τουλάχιστον 8 χαρακτήρες."))
    #             elif "numeric" in str(error):
    #                 error_messages.append(_("Ο κωδικός πρόσβασης δεν μπορεί να περιέχει μόνο αριθμούς."))
    #             elif "personal information" in str(error):
    #                 error_messages.append(_("Ο κωδικός πρόσβασης δεν μπορεί να έχει μεγάλη ομοιότητα με άλλες προσωπικές πληροφορίες."))

    #         if error_messages:
    #             raise forms.ValidationError(error_messages)

    #     return password
    