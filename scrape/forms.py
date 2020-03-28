from django import forms

class NameForm(forms.Form):
    hotel_name = forms.CharField(label='Hotel Name', max_length=100)