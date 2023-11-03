from allauth.account.adapter import DefaultAccountAdapter
from django.forms import ValidationError

class RestrictEmailAdapter(DefaultAccountAdapter):

    def clean_email(self,email):
        if not email.endswith('@sch.gr'):
            raise ValidationError('Μπορείτε να κάνετε εγγραφή μόνο με email που ανήκει στο domain sch.gr')
        return email