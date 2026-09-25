from io import StringIO

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from core.models import ActivityLog, CustomUser, OrganizationalUnit, PermissionCode, Role
from core.permissions import sync_kadrovi_permissions, sync_pravna_resenja_permissions
from core.user_access import UserAccessForm
from hr.access import visible_employees
from hr.models import Employee
from hr.permissions import collect_kadrovi_permission_codes


class UserAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_superuser('access-admin', 'admin@example.com', 'test')
        cls.account = CustomUser.objects.create_user('access-user')
        cls.unit = OrganizationalUnit.objects.create(code='430001   ', center='43   ', name='Laboratorija')
        cls.role = Role.objects.create(name='Test uloga', slug='test-uloga')
        cls.permission = PermissionCode.objects.create(code='employee_list')
        cls.role.permissions.add(cls.permission)

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse('user_access_edit',args=[self.account.pk])

    def payload(self, **extra):
        return {'first_name':'Novo', 'last_name':'Ime', 'email':'', 'is_active':'on',
                'roles':[self.role.pk], 'center_codes':['43'], 'allowed_centers':[self.unit.pk], **extra}

    def test_screen_uses_application_form_and_normalized_choices(self):
        response = self.client.get(self.url)
        self.assertContains(response,'Sačuvaj pristup')
        self.assertNotContains(response,'Kadrovske organizacione jedinice')  # uklonjeno 25.09.2026.
        self.assertIn(('43','Centar 43'),response.context['form'].fields['center_codes'].choices)
        self.assertNotContains(response,'name="is_superuser"')

    def test_save_roles_scopes_status_and_audit_without_privilege_escalation(self):
        response = self.client.post(self.url,self.payload(is_superuser='on',is_staff='on'))
        self.assertRedirects(response,self.url)
        self.account.refresh_from_db()
        self.assertEqual(self.account.allowed_center_codes,'43')
        self.assertEqual(list(self.account.roles.all()),[self.role])
        self.assertEqual(list(self.account.allowed_centers.all()),[self.unit])
        self.assertFalse(self.account.is_superuser)
        self.assertFalse(self.account.is_staff)
        log=ActivityLog.objects.get(action=ActivityLog.ACTION_MANUAL,object_pk=str(self.account.pk))
        self.assertEqual(log.changes['before']['roles'],[])
        self.assertEqual(log.changes['after']['roles'],['test-uloga'])

    def test_unknown_center_and_unit_leave_entire_account_unchanged(self):
        response=self.client.post(self.url,self.payload(center_codes=['999'],allowed_centers=['999999']))
        self.assertEqual(response.status_code,200)
        self.account.refresh_from_db()
        self.assertEqual(self.account.first_name,'')
        self.assertFalse(self.account.roles.exists())
        self.assertFalse(self.account.allowed_centers.exists())

    def test_existing_outdated_center_is_preserved_on_round_trip(self):
        self.account.allowed_center_codes=' 99;43, '
        self.account.save()
        response=self.client.post(self.url,self.payload(center_codes=['99','43']))
        self.assertEqual(response.status_code,302)
        self.account.refresh_from_db()
        self.assertEqual(self.account.allowed_center_codes,'43,99')

    def test_regular_staff_and_role_grant_do_not_allow_account_changes(self):
        self.account.is_staff=True
        self.account.save()
        self.role.permissions.add(PermissionCode.objects.create(code='user_access_edit'))
        self.account.roles.add(self.role)
        self.client.force_login(self.account)
        self.assertEqual(self.client.get(self.url).status_code,403)
        self.assertEqual(self.client.post(self.url,self.payload()).status_code,403)

    def test_user_list_is_no_longer_visible_to_any_logged_in_account(self):
        self.client.force_login(self.account)
        self.assertEqual(self.client.get(reverse('user_list')).status_code,403)

    def test_inactive_role_does_not_pass_legacy_role_mixin(self):
        from types import SimpleNamespace
        from core.mixins import RoleRequiredMixin
        self.account.roles.add(self.role)
        view=RoleRequiredMixin()
        view.required_roles=[self.role.slug]
        view.request=SimpleNamespace(user=self.account)
        self.assertTrue(view.test_func())
        self.role.is_active=False;self.role.save()
        self.assertFalse(view.test_func())

    def test_anonymous_and_csrf_are_enforced(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code,302)
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.url,self.payload()).status_code,403)

    def test_cannot_disable_own_superuser_account(self):
        response=self.client.post(reverse('user_access_edit',args=[self.admin.pk]),self.payload(is_active=''))
        self.assertEqual(response.status_code,302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_removing_role_also_removes_legacy_group_that_would_restore_it(self):
        role=Role.objects.create(slug='sekretarijat',name='Sekretarijat')
        group=Group.objects.create(name='Sekretarijat')
        self.account.roles.add(role)
        self.account.groups.add(group)
        self.client.post(self.url,self.payload(roles=[]))
        self.assertFalse(self.account.groups.filter(pk=group.pk).exists())
        self.assertFalse(self.account.roles.exists())


class KadroviRoleTests(TestCase):
    def setUp(self):
        Role.objects.filter(slug__in=['kadrovik-resenja','kadrovi']).delete()

    def test_rename_preserves_user_and_additional_permission_and_inactive_state(self):
        old=Role.objects.create(name='Kadrovik — rešenja',slug='kadrovik-resenja',is_active=False)
        permission=PermissionCode.objects.create(code='custom:keep')
        old.permissions.add(permission)
        user=CustomUser.objects.create_user('old-kadrovi')
        user.roles.add(old)
        result=sync_kadrovi_permissions()
        role=result['role']
        self.assertEqual(role.pk,old.pk)
        self.assertEqual(role.name,'Kadrovi')
        self.assertFalse(role.is_active)
        self.assertTrue(user.roles.filter(slug='kadrovi').exists())
        self.assertTrue(role.permissions.filter(code='custom:keep').exists())
        self.assertTrue(set(collect_kadrovi_permission_codes()) <= set(role.permissions.values_list('code',flat=True)))
        self.assertFalse(role.permissions.filter(code__in=['hr:resenje_view_all','hr:evaluation_view_all','user_access_edit']).exists())
        sync_pravna_resenja_permissions()
        self.assertFalse(Role.objects.filter(slug='kadrovik-resenja').exists())

    def test_merge_existing_roles_transfers_members_without_losing_permissions(self):
        role=Role.objects.create(name='Kadrovi',slug='kadrovi')
        old=Role.objects.create(name='Kadrovik — rešenja',slug='kadrovik-resenja')
        user=CustomUser.objects.create_user('merge-user');user.roles.add(old)
        permission=PermissionCode.objects.create(code='extra:keep');old.permissions.add(permission)
        sync_kadrovi_permissions()
        self.assertEqual(list(user.roles.all()),[role])
        self.assertTrue(role.permissions.filter(pk=permission.pk).exists())
        self.assertEqual(sync_kadrovi_permissions()['granted'],0)

    def test_dry_run_does_not_rename_role(self):
        old=Role.objects.create(name='Kadrovik — rešenja',slug='kadrovik-resenja')
        call_command('sync_pravna_resenja_permissions',dry_run=True,stdout=StringIO())
        old.refresh_from_db()
        self.assertEqual(old.slug,'kadrovik-resenja')


class KadroviScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role=sync_kadrovi_permissions()['role']
        cls.user=CustomUser.objects.create_user('scoped-kadrovi',allowed_center_codes='43')
        cls.user.roles.add(cls.role)
        OrganizationalUnit.objects.create(code='430001 ',center='43 ',name='Posao 43')
        OrganizationalUnit.objects.create(code='410001 ',center='41 ',name='Posao 41')
        cls.employees=[]
        for index,code in enumerate(['431','432','411']):
            cls.employees.append(Employee.objects.create(employee_code=9000+index,first_name='Ime',last_name=code,
                position='Referent',department_code=int(code),org_unit_code=code,gender='M',
                date_of_birth='1990-01-01',date_of_joining='2026-01-01',personal_number=f'010199000000{index}'))

    def test_center_contains_hr_units_but_not_another_center(self):
        self.assertEqual(set(visible_employees(self.user)),set(self.employees[:2]))

    def test_kadrovi_without_scope_sees_no_other_employees(self):
        self.user.allowed_center_codes='';self.user.save()
        self.assertFalse(visible_employees(self.user).exists())

    def test_list_and_direct_employee_edit_respect_scope(self):
        self.client.force_login(self.user)
        response=self.client.get(reverse('employee_list'))
        self.assertEqual(set(response.context['employees']),set(self.employees[:2]))
        self.assertEqual(self.client.get(reverse('employee_update',args=[self.employees[2].pk])).status_code,404)

    def test_work_sheet_foreign_center_is_rejected_before_creating_sheet(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('hr:employee_work_time_sheet',args=[self.employees[2].pk])).status_code,404)

    def test_resenje_employee_suggestion_does_not_leak_another_center(self):
        self.client.force_login(self.user)
        response=self.client.get(reverse('hr:resenje_predlog'),{'zaposleni':self.employees[2].pk})
        self.assertEqual(response.json(),{'zaposleni_tekst':'','oj_naziv':''})

    def test_evaluation_manager_has_only_assigned_employees(self):
        from hr.services.evaluations import editable_employees
        self.assertEqual(set(editable_employees(self.user)),set(self.employees[:2]))

    def _zahtev_za_resenje(self, employee):
        from hr.models import Zahtev, VrstaZahteva
        number = Zahtev.objects.count() + 1
        return Zahtev.objects.create(vrsta=VrstaZahteva.objects.first(), zaposleni=employee,
            godina=2026, redni_broj=number, broj=f'T-{number}', datum_zahteva='2026-09-24',
            podnosilac=employee, odobrava=employee, created_by=self.user)

    def test_resenja_use_snapshot_scope_not_employee_current_center(self):
        from hr.models import VrstaResenja, Resenje
        from hr.services.resenja import visible_resenja
        kind=VrstaResenja.objects.first()
        if kind is None:
            kind=VrstaResenja.objects.create(kod='scope-test',naziv='Test',naslov='Test')
        owned=Resenje.objects.create(zahtev=self._zahtev_za_resenje(self.employees[0]), zaposleni=self.employees[2],vrsta=kind,broj='S-1',datum_resenja='2026-09-24',
            created_by=self.user,oj_kod='431',centar='43 ')
        Resenje.objects.create(zahtev=self._zahtev_za_resenje(self.employees[0]), zaposleni=self.employees[0],vrsta=kind,broj='S-2',datum_resenja='2026-09-24',
            created_by=self.user,oj_kod='411',centar='41')
        self.assertEqual(list(visible_resenja(self.user)),[owned])

    def test_resenja_with_empty_center_are_visible_by_allowed_hr_unit(self):
        from hr.models import VrstaResenja, Resenje
        kind = VrstaResenja.objects.first()
        owned = Resenje.objects.create(zahtev=self._zahtev_za_resenje(self.employees[0]), zaposleni=self.employees[0], vrsta=kind, broj='OJ-1',
            datum_resenja='2026-09-24', oj_kod='431 ', centar='', created_by=self.user)
        hidden = Resenje.objects.create(zahtev=self._zahtev_za_resenje(self.employees[0]), zaposleni=self.employees[2], vrsta=kind, broj='OJ-2',
            datum_resenja='2026-09-24', oj_kod='411', centar='', created_by=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse('hr:resenje_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['resenja']), [owned])
        self.assertContains(response, reverse('hr:resenje_list'))
        self.assertEqual(self.client.get(reverse('hr:resenje_detail', args=[owned.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('hr:resenje_detail', args=[hidden.pk])).status_code, 404)

    def test_resenje_form_limits_unit_choices_to_assigned_scope(self):
        from hr.resenja_forms import ResenjeForm
        form = ResenjeForm(actor=self.user)
        codes = dict(form.fields['oj_kod'].choices)
        self.assertIn('431', codes)
        self.assertNotIn('411', codes)

    def test_operational_role_cannot_register_signers_through_draft_form(self):
        from hr.resenja_forms import ResenjeForm
        user = CustomUser.objects.create_user('resenja-operativno')
        role = Role.objects.create(slug='operativno', name='Operativno')
        role.permissions.add(PermissionCode.objects.get(code='hr:resenje_create'))
        user.roles.add(role)
        form = ResenjeForm({'novi_potpisnik': self.employees[0].pk}, actor=user)
        self.assertNotIn('novi_potpisnik', form.fields)
        self.assertFalse(form.can_add_signer)
