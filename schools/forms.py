from django import forms
from .models import School, SchoolUser

class SchoolUserForm(forms.ModelForm):
    class Meta:
        model = SchoolUser
        fields = ('department', 'school', 'address', 'address_number', 'city', 'zipcode', 'phone', 'director_name', 'director_surname', 'privacy_accepted')
        labels = {
            'department': 'ΠΕΡΙΦΕΡΕΙΑΚΗ ΔΙΕΥΘΥΝΣΗ',
            'school': 'ΟΝΟΜΑ ΣΧΟΛΕΙΟΥ',
            'address': 'ΔΙΕΥΘΥΝΣΗ',
            'address_number': 'ΑΡΙΘΜΟΣ',
            'city': 'ΠΟΛΗ',
            'zipcode': 'ΤΚ',
            'phone': 'ΤΗΛΕΦΩΝΟ',
            'director_name': 'ΟΝΟΜΑ ΔΙΕΥΘΥΝΤΗ',
            'director_surname': 'ΕΠΩΝΥΜΟ ΔΙΕΥΘΥΝΤΗ',
            'privacy_accepted': 'ΑΠΟΔΟΧΗ ΟΡΩΝ',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['school'].queryset = SchoolUser.objects.none()

        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['school'].queryset = School.objects.filter(department_id=department_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty School queryset
        elif self.instance.pk:
            self.fields['school'].queryset = self.instance.department.school_set.order_by('name')


class SchoolUserUpdateForm(forms.ModelForm):
    class Meta:
        model = SchoolUser
        fields = ('director_name', 'director_surname')
