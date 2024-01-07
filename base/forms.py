from django import forms

class SchoolSearchForm(forms.Form):
    q = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q'].widget.attrs.update(
            {'class': 'form-control menudd'})
        self.fields['q'].widget.attrs.update(
            {'data-toggle': 'dropdown'})