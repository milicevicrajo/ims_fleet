from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils import timezone
from .models import (FinancePartnerIdentity, CollectionContact, ContactPoint, CollectionActivity,
                     CollectionNotice, CollectionNoticeItem, CollectionProfile, CollectionLegalCase, CollectionLegalEvent)
from .services.contacts import clean_phone


class AmountField(forms.DecimalField):
    def to_python(self, value):
        if isinstance(value, str):
            value = value.replace(' ', '').replace('\u00a0', '')
            if ',' in value and '.' in value:
                value = value.replace('.', '').replace(',', '.') if value.rfind(',') > value.rfind('.') else value.replace(',', '')
            elif ',' in value: value = value.replace(',', '.')
        return super().to_python(value)


class CollectionForm(forms.ModelForm):
    version = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk: self.fields['version'].initial = self.instance.updated_at.isoformat()
        for name, field in list(self.fields.items()):
            if isinstance(field, forms.DecimalField):
                field = self.fields[name] = AmountField(max_digits=field.max_digits, decimal_places=field.decimal_places, required=field.required, label=field.label)
            if isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'})
                field.input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%d.%m.%Y %H:%M']
            elif isinstance(field, forms.DateField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
                field.input_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d.%m.%Y.']
            if isinstance(field.widget, forms.Textarea): field.widget.attrs['rows'] = 3
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs['class'] = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
        if 'identity' in self.fields:
            field = self.fields['identity'];field.label = 'Partner';field.required = True
            field.label_from_instance = lambda obj: f'{obj.partner_code} · {obj.source_name}'
            value = self.data.get('identity') if self.is_bound else self.initial.get('identity', self.instance.identity_id)
            if isinstance(value, FinancePartnerIdentity): value = value.pk
            try: value = int(value) if value else None
            except (TypeError, ValueError): value = None
            field.queryset = FinancePartnerIdentity.objects.filter(company=1, partner_group=1, pk=value)
            field.widget.attrs.update({'class': 'form-control collection-partner-select'})

    def clean(self):
        values = super().clean()
        if self.instance.pk and values.get('version') != self.instance.updated_at.isoformat():
            raise ValidationError('Zapis je u međuvremenu promenjen. Otvorite ga ponovo pre čuvanja.')
        return values


class ContactForm(CollectionForm):
    class Meta:
        model = CollectionContact
        fields = ['identity', 'first_name', 'last_name', 'position', 'note', 'needs_review']
        labels = {'first_name':'Ime', 'last_name':'Prezime', 'position':'Funkcija / odeljenje', 'note': 'Napomena', 'needs_review': 'Potrebna provera kontakta'}

    def clean(self):
        values = super().clean()
        if not any(values.get(x) for x in ('first_name', 'last_name', 'position')):
            raise ValidationError('Unesite ime osobe ili funkciju / odeljenje za opšti kontakt.')
        return values


class PointForm(forms.ModelForm):
    class Meta:
        model = ContactPoint
        fields = ['kind', 'value', 'label']
        widgets = {k: forms.TextInput(attrs={'class': 'form-control'}) for k in ['value', 'label']}

    def clean(self):
        values = super().clean()
        value = values.get('value', '').strip()
        if not value or values.get('DELETE'): return values
        if values.get('kind') == 'email':
            validate_email(value);value = value.lower()
        else:
            value = clean_phone(value)
        values['value'] = value
        return values


class CollectionInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if 'DELETE' in form.fields: form.fields['DELETE'].label = 'Ukloni red'


ContactPointFormSet = inlineformset_factory(CollectionContact, ContactPoint, form=PointForm, formset=CollectionInlineFormSet, extra=2, can_delete=True, max_num=50, validate_max=True)


class ActivityForm(CollectionForm):
    class Meta:
        model = CollectionActivity
        fields = ['identity', 'kind', 'contact', 'occurred_at', 'text', 'outcome', 'next_action_date']
        labels = {'kind': 'Vrsta', 'contact': 'Kontakt osoba', 'occurred_at': 'Datum i vreme', 'text': 'Napomena / sadržaj razgovora', 'outcome': 'Ishod', 'next_action_date': 'Sledeći kontakt'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        identity = self.data.get('identity') if self.is_bound else self.initial.get('identity', self.instance.identity_id)
        try: identity = int(identity) if identity else None
        except (ValueError, TypeError): identity = None
        self.fields['contact'].queryset = CollectionContact.objects.filter(identity_id=identity, active=True) if identity else CollectionContact.objects.none()
        self.fields['contact'].label_from_instance = lambda obj: obj.name or obj.position or f'Kontakt #{obj.pk}'
        self.fields['text'].required = True
        self.fields['occurred_at'].required = True
        if not self.instance.pk: self.initial.setdefault('occurred_at', timezone.localtime())

    def clean(self):
        values = super().clean()
        contact, identity = values.get('contact'), values.get('identity')
        if contact and identity and contact.identity_id != identity.pk:
            self.add_error('contact', 'Kontakt mora pripadati izabranom partneru.')
        return values


class NoticeForm(CollectionForm):
    currency = forms.ChoiceField(label='Valuta', choices=[('RSD', 'RSD'), ('EUR', 'EUR'), ('USD', 'USD')])
    class Meta:
        model = CollectionNotice
        fields = ['identity', 'kind', 'year', 'number', 'issued_on', 'total_amount', 'currency', 'recipient', 'response_due_date', 'body', 'original_invoice_text', 'note']
        labels = {'kind': 'Vrsta dokumenta', 'year': 'Godina', 'number': 'Broj', 'issued_on': 'Datum', 'total_amount': 'Ukupan iznos', 'original_invoice_text': 'Dodatne / nasleđene reference faktura', 'note': 'Interna napomena', 'recipient':'Primalac', 'body':'Tekst dokumenta', 'response_due_date':'Rok za odgovor / uplatu'}
        widgets = {'original_invoice_text': forms.Textarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('issued_on', 'number'): self.fields[name].required = True
        if not self.instance.pk:
            self.initial.setdefault('issued_on', timezone.localdate())
            self.initial.setdefault('year', timezone.localdate().year)
            self.initial.setdefault('currency', 'RSD')

    def clean(self):
        values = super().clean()
        if values.get('issued_on'):
            if values.get('year') and values['year'] != values['issued_on'].year:
                self.add_error('year', 'Godina mora odgovarati datumu dokumenta.')
            values['year'] = values['issued_on'].year
        if values.get('response_due_date') and values.get('issued_on') and values['response_due_date'] < values['issued_on']:
            self.add_error('response_due_date', 'Rok ne može biti pre datuma dokumenta.')
        return values


class NoticeItemForm(forms.ModelForm):
    amount_snapshot = AmountField(label='Iznos', max_digits=18, decimal_places=2, required=True)
    due_date_snapshot = forms.DateField(label='Dospeće', required=False, input_formats=['%Y-%m-%d', '%d.%m.%Y', '%d.%m.%Y.'], widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    class Meta:
        model = CollectionNoticeItem
        fields = ['original_reference', 'job_code', 'due_date_snapshot', 'amount_snapshot']
        labels = {'original_reference': 'Faktura / dokument', 'job_code': 'Šifra posla'}

    def clean_original_reference(self):
        value = self.cleaned_data['original_reference'].strip()
        if not value: raise ValidationError('Unesite referencu dokumenta.')
        return value


NoticeItemFormSet = inlineformset_factory(CollectionNotice, CollectionNoticeItem, form=NoticeItemForm, formset=CollectionInlineFormSet, extra=2, can_delete=True, max_num=500, validate_max=True)


class ProfileForm(CollectionForm):
    class Meta:
        model = CollectionProfile
        fields = ['important_customer', 'needs_review', 'review_note']
        labels = {'important_customer': 'Važan kupac', 'needs_review': 'Za proveru', 'review_note': 'Razlog / napomena za proveru'}


class LegalCaseForm(CollectionForm):
    class Meta:
        model = CollectionLegalCase
        fields = ['identity', 'tip', 'sud', 'broj_predmeta', 'valuta', 'osnovni_dug', 'izvrsiteljski_broj', 'datum_pokretanja',
                  'predmet_spora', 'tuzilac', 'vrednost_spora', 'datum_podnosenja_tuzbe', 'vece', 'kamata', 'troskovi', 'ukupan_dug',
                  'datum_otvaranja_stecaja', 'prijava_potrazivanja', 'novi_broj', 'pib']


class LegalEventForm(CollectionForm):
    class Meta:
        model = CollectionLegalEvent
        fields = ['date', 'text']
        labels = {'date':'Datum', 'text':'Promena / opis'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk: self.initial.setdefault('date', timezone.localdate())
