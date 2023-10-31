from django import forms
from .models import School, SchoolUser

class SchoolUserForm(forms.ModelForm):
    class Meta:
        model = SchoolUser
        fields = ('department', 'school', 'address', 'address_number', 'city', 'zipcode', 'phone', 'email', 'director_name', 'director_surname', 'privacy_accepted')

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