from django import forms
from schools.models import School, SchoolUser

class SchoolUserUpdateForm(forms.ModelForm):
    class Meta:
        model = SchoolUser
        fields = ('address', 'address_number', 'city', 'zipcode', 'phone', 'director_name', 'director_surname')
        labels = {
            # 'department': 'ΠΕΡΙΦΕΡΕΙΑΚΗ ΔΙΕΥΘΥΝΣΗ',
            # 'school': 'ΟΝΟΜΑ ΣΧΟΛΕΙΟΥ',
            'address': 'ΔΙΕΥΘΥΝΣΗ',
            'address_number': 'ΑΡΙΘΜΟΣ',
            'city': 'ΠΟΛΗ',
            'zipcode': 'ΤΚ',
            'phone': 'ΤΗΛΕΦΩΝΟ',
            'director_name': 'ΟΝΟΜΑ ΔΙΕΥΘΥΝΤΗ',
            'director_surname': 'ΕΠΩΝΥΜΟ ΔΙΕΥΘΥΝΤΗ',
            # 'privacy_accepted': 'ΑΠΟΔΟΧΗ ΟΡΩΝ',
        }