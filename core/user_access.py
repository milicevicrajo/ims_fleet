"""Administracija korisničkog pristupa kroz aplikaciju."""
from django import forms
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q

from core.activity import log_activity
from core.models import CustomUser, Role


def access_snapshot(account):
    # Obuhvat se od 28.09.2026. vodi na ekranu Organizacija → Dodele uloga (sopstvena istorija).
    return {
        'roles': list(account.roles.order_by('slug').values_list('slug', flat=True)),
        'is_active': account.is_active,
    }


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
    """Nalog i uloge. Obuhvat podataka (centri, jedinice, sifre) se od 28.09.2026. dodeljuje na ekranu
    Organizacija → Dodele uloga; stara polja `allowed_center_codes` i `allowed_centers` se ovde vise
    ne menjaju (stara organizacija je ugasena)."""
    roles = RoleChoiceField(label='Uloge', queryset=Role.objects.none(), required=False)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'is_active', 'roles')
        labels = {'first_name': 'Ime', 'last_name': 'Prezime', 'email': 'E-pošta', 'is_active': 'Aktivan nalog'}

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields['roles'].queryset = Role.objects.filter(
            Q(is_active=True) | Q(users=self.instance)).distinct().order_by('name')
        for name, field in self.fields.items():
            field.widget.attrs['class'] = ('form-check-input' if name=='is_active' else
                'form-select select2-method' if isinstance(field, forms.MultipleChoiceField) or isinstance(field, forms.ModelMultipleChoiceField) else 'form-control')
        if self.instance.pk == actor.pk:
            self.fields['is_active'].disabled = True

    @transaction.atomic
    def save(self, commit=True, *, request=None):
        if not commit:
            raise ValueError('Korisnički pristup se uvek čuva zajedno sa ulogama i obuhvatom.')
        # Zaključavanje i snimak iz baze: ModelForm je već promenio instance polja.
        previous = CustomUser.objects.select_for_update().get(pk=self.instance.pk)
        before = access_snapshot(previous)
        account = super().save(commit=False)
        account.save(update_fields=['first_name','last_name','email','is_active'])
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
