from django import forms

from core.models import OrganizationalUnit


class OrganizationalUnitForm(forms.ModelForm):
    class Meta:
        model = OrganizationalUnit
        fields = "__all__"
