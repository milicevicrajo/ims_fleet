from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PermissionCode, Role, RolePermission


class MeniceSmokeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="menice-test",
            password="test-password",
        )
        role = Role.objects.create(name="Menice", slug="menice")
        for code in ["menice:menica_list", "menice:ulazna_menica_create"]:
            permission = PermissionCode.objects.create(code=code)
            RolePermission.objects.create(role=role, permission=permission)
        self.user.roles.add(role)
        self.client.force_login(self.user)

    def test_izlazne_list_page_renders(self):
        response = self.client.get(reverse("menice:menica_list", kwargs={"tip": "izlazna"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Izlazne menice")

    def test_ulazna_create_page_renders(self):
        response = self.client.get(reverse("menice:ulazna_menica_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nova - Ulazna menica")
