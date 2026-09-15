from datetime import date

from django import forms
from django.utils import timezone

from hr.models import Employee, EvaluationGroup
from hr.services.evaluations import editable_employees, latin, MONTHS


class CoefficientField(forms.DecimalField):
    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace(',', '.')
        return super().to_python(value)


def style_form(form):
    for field in form.fields.values():
        if isinstance(field, forms.BooleanField):
            field.widget.attrs['class'] = 'form-check-input'
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs['class'] = 'form-control form-select select2-method'
        elif not isinstance(field.widget, forms.HiddenInput):
            field.widget.attrs['class'] = 'form-control'


class EvaluationHeaderForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.none(), label='Zaposleni')
    month = forms.TypedChoiceField(coerce=int, choices=list(enumerate(MONTHS, 1)), label='Mesec rezultata')
    year = forms.IntegerField(min_value=2000, max_value=2100, label='Godina')
    group = forms.ModelChoiceField(queryset=EvaluationGroup.objects.filter(is_active=True), label='Grupa za ocenjivanje')
    supervisor = forms.ModelChoiceField(queryset=Employee.objects.all(), label='Neposredni rukovodilac')
    director = forms.ModelChoiceField(queryset=Employee.objects.all(), label='Direktor centra')
    general_director = forms.ModelChoiceField(queryset=Employee.objects.all(), label='Generalni direktor')

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = editable_employees(user)
        for field in ['employee', 'supervisor', 'director', 'general_director']:
            self.fields[field].label_from_instance = lambda employee: f'{employee.employee_code} - {latin(employee)}'
        style_form(self)

    def clean(self):
        data = super().clean()
        employee = data.get('employee')
        if employee:
            for field in ['supervisor', 'director', 'general_director']:
                if data.get(field) == employee:
                    self.add_error(field, 'Ocenjivač mora biti druga osoba od ocenjenog zaposlenog.')
        return data


class EvaluationValuesForm(forms.Form):
    snapshot_token = forms.CharField(widget=forms.HiddenInput)
    comment = forms.CharField(required=False, max_length=4000, label='Opšti komentar', widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, snapshot, token=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['snapshot_token'].initial = token
        self.fields['comment'].initial = latin(snapshot.get('comment', ''))
        for item in snapshot['items']:
            choices = [(str(option['points']), f"{option['points']} - {option['value'].replace('.', ',')}") for option in sorted(item['options'], key=lambda value: value['points'], reverse=True)]
            name = f'criterion_{item["code"]}'
            self.fields[name] = forms.ChoiceField(choices=choices, label=latin(item['name']), initial=str(item['points']))
            self.fields[name].widget.attrs.update({'class': 'form-control form-select evaluation-points', 'data-code': item['code']})
            self.fields[f'comment_{item["code"]}'] = forms.CharField(required=False, max_length=2000, label='Komentar ocenjivača',
                initial=latin(item.get('comment', '')), widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
        self.fields['comment'].widget.attrs['class'] = 'form-control'
        self.rows = [{'item': item, 'choice': self[f'criterion_{item["code"]}'], 'comment': self[f'comment_{item["code"]}']} for item in snapshot['items']]


class EvaluationApprovalForm(forms.Form):
    stage = forms.ChoiceField(label='Nivo saglasnosti', choices=[
        ('supervisor', 'Neposredni rukovodilac'),
        ('director', 'Direktor centra'),
        ('general_director', 'Generalni direktor'),
    ])
    document_date = forms.DateField(label='Datum na obrascu', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    coefficient = CoefficientField(required=False, max_digits=10, decimal_places=5, label='Konačni koeficijent (opciona korekcija)',
        widget=forms.TextInput(attrs={'inputmode': 'decimal'}))
    comment = forms.CharField(required=False, max_length=4000, label='Obrazloženje / komentar', widget=forms.Textarea(attrs={'rows': 2}))
    confirm = forms.BooleanField(label='Saglasan/saglasna sam sa ovom verzijom i navedenim koeficijentom.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields['document_date'].initial = date(today.year, today.month, 15)
        style_form(self)
