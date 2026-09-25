"""Administracija korisničkog pristupa kroz aplikaciju."""
from django import forms
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q

from core.activity import log_activity
from core.models import CustomUser, OrganizationalUnit, Role
from hr.models import Employee


def split_codes(raw):
    return sorted({part.strip() for part in (raw or '').replace(';', ',').split(',') if part.strip()})


def access_snapshot(account):
    return {
        'roles': list(account.roles.order_by('slug').values_list('slug', flat=True)),
        'centers': split_codes(account.allowed_center_codes),
        'units': list(account.allowed_centers.order_by('pk').values_list('pk', flat=True)),
        'hr_units': account.allowed_hr_unit_codes,
        'is_active': account.is_active,
    }


class UnitChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.code.strip()} — {obj.name.strip()} (centar {obj.center.strip()})'


class RoleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name + ('' if obj.is_active else ' (neaktivna)')


def permission_label(permission):
    return permission.label or {
        'employee_list':'Zaposleni — spisak', 'employee_detail':'Zaposleni — detalji',
        'employee_create':'Zaposleni — unos', 'employee_update':'Zaposleni — izmena',
        'employee_sync':'Zaposleni — sinhronizacija',
        'hr:kadrovi_manage':'Kadrovi — upravljanje podacima dodeljenih centara i OJ',
        'hr:employee_work_time_sheet':'Radne liste drugih zaposlenih u obuhvatu',
        'hr:work_time_sheet':'Sopstvena radna lista', 'hr:work_time_sheet_print':'Radna lista — štampa',
        'hr:evaluation_detail':'Ocenjivanje — detalji', 'hr:evaluation_print':'Ocenjivanje — štampa',
        'hr:evaluation_catalog_create':'Ocenjivanje — unos u šifarnik',
        'hr:evaluation_catalog_edit':'Ocenjivanje — izmena šifarnika',
        'hr:evaluation_bulk_approve':'Ocenjivanje — grupna saglasnost imenovanog ocenjivača',
        'user_list':'Korisnici — pregled', 'user_access_edit':'Korisnici — upravljanje pristupom (superuser)',
    }.get(permission.code, permission.code)


class UserAccessForm(forms.ModelForm):
    center_codes = forms.MultipleChoiceField(label='Centri', required=False)
    hr_unit_codes = forms.MultipleChoiceField(label='Kadrovske organizacione jedinice', required=False)
    roles = RoleChoiceField(label='Uloge', queryset=Role.objects.none(), required=False)
    allowed_centers = UnitChoiceField(label='Organizacione jedinice i poslovi iz postojećeg šifarnika',
                                     queryset=OrganizationalUnit.objects.none(), required=False)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'is_active', 'roles', 'allowed_centers')
        labels = {'first_name': 'Ime', 'last_name': 'Prezime', 'email': 'E-pošta', 'is_active': 'Aktivan nalog'}

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields['roles'].queryset = Role.objects.filter(
            Q(is_active=True) | Q(users=self.instance)).distinct().order_by('name')
        self.fields['allowed_centers'].queryset = OrganizationalUnit.objects.order_by('center','code')
        centers = {str(c).strip() for c in OrganizationalUnit.objects.values_list('center',flat=True) if c and str(c).strip()}
        centers.update(split_codes(self.instance.allowed_center_codes))
        from fleet.support.registar import Registar
        registar = Registar()
        self.fields['center_codes'].choices = [
            (c, f'Centar {registar.oznaka_centra(c)}') for c in sorted(centers, key=lambda x: (len(x), x))]
        if registar.dostupan:
            # Aktivne sifre iz registra; vec dodeljene ostaju u izboru, jer postojeca prava ne smeju da nestanu.
            from fleet.support.registar import ogranici_izbor
            dodeljene = set(self.instance.allowed_centers.values_list('pk', flat=True)) if self.instance.pk else set()
            ogranici_izbor(self.fields['allowed_centers'], registar=registar, zadrzi=dodeljene)
        units = {str(c or d or '').strip() for c,d in Employee.objects.values_list('org_unit_code','department_code')}
        units.update(self.instance.allowed_hr_unit_codes or [])
        self.fields['hr_unit_codes'].choices = [(c, f'OJ {c}') for c in sorted(units - {''},key=lambda x:(len(x),x))]
        self.initial['center_codes'] = split_codes(self.instance.allowed_center_codes)
        self.initial['hr_unit_codes'] = self.instance.allowed_hr_unit_codes or []
        for name, field in self.fields.items():
            field.widget.attrs['class'] = ('form-check-input' if name=='is_active' else
                'form-select select2-method' if isinstance(field, forms.MultipleChoiceField) or isinstance(field, forms.ModelMultipleChoiceField) else 'form-control')
        if self.instance.pk == actor.pk:
            self.fields['is_active'].disabled = True

    def clean_center_codes(self):
        values = sorted(set(self.cleaned_data['center_codes']))
        if len(','.join(values)) > 255:
            raise forms.ValidationError('Izabrane šifre prelaze dozvoljenu dužinu od 255 znakova.')
        return values

    @transaction.atomic
    def save(self, commit=True, *, request=None):
        if not commit:
            raise ValueError('Korisnički pristup se uvek čuva zajedno sa ulogama i obuhvatom.')
        # Zaključavanje i snimak iz baze: ModelForm je već promenio instance polja.
        previous = CustomUser.objects.select_for_update().get(pk=self.instance.pk)
        before = access_snapshot(previous)
        account = super().save(commit=False)
        account.allowed_center_codes = ','.join(self.cleaned_data['center_codes'])
        account.allowed_hr_unit_codes = self.cleaned_data['hr_unit_codes']
        account.save(update_fields=['first_name','last_name','email','is_active','allowed_center_codes','allowed_hr_unit_codes'])
        self.save_m2m()
        # Noćni sync prevodi ove stare Django grupe u uloge; uklanjanje uloge mora opstati.
        selected = set(account.roles.values_list('slug', flat=True))
        for name, slug in [('Sekretarijat','sekretarijat'),('Zaposleni','zaposleni'),('Pregled naplate','pregled-naplate')]:
            if slug not in selected:
                account.groups.remove(*Group.objects.filter(name__iexact=name))
        log_activity(request=request, user=self.actor, object_instance=account,
            description=f'Izmenjen pristup korisnika {account.username}',
            changes={'before':before,'after':access_snapshot(account)})
        if request is not None:
            request._skip_activity_log = True
        return account
