from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import reverse

from lung_cancer_care.changelog import DEFAULT_CHANGELOG_TEMPLATE, get_changelog_page_context


class _StaffUser:
    is_active = True
    is_staff = True
    is_anonymous = False
    is_authenticated = True

    def get_short_name(self):
        return ""

    def get_username(self):
        return "staff"

    def has_usable_password(self):
        return False

    def has_perm(self, perm):
        return True

    def has_perms(self, perms):
        return True

    def has_module_perms(self, app_label):
        return True


class AdminChangelogTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_missing_changelog_file_is_created_from_template(self):
        with TemporaryDirectory() as tmpdir:
            changelog_path = Path(tmpdir) / "CHANGELOG.md"
            with override_settings(CHANGELOG_PATH=changelog_path):
                context = get_changelog_page_context()

            self.assertTrue(changelog_path.exists())
            self.assertTrue(context["changelog_file_created"])
            self.assertEqual(changelog_path.read_text(encoding="utf-8"), DEFAULT_CHANGELOG_TEMPLATE)

    def test_admin_changelog_requires_staff_access(self):
        request = self.factory.get(reverse("admin:changelog"))
        request.user = AnonymousUser()

        response = admin.site.admin_view(admin.site.changelog_view)(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_staff_user_can_view_rendered_changelog(self):
        with TemporaryDirectory() as tmpdir:
            changelog_path = Path(tmpdir) / "CHANGELOG.md"
            changelog_path.write_text(
                "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- Admin changelog page.\n",
                encoding="utf-8",
            )
            with override_settings(CHANGELOG_PATH=changelog_path):
                request = self.factory.get(reverse("admin:changelog"))
                request.user = _StaffUser()

                response = admin.site.admin_view(admin.site.changelog_view)(request)
                response.render()

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "返回后台首页")
        self.assertNotContains(response, str(changelog_path))
        self.assertContains(response, "Admin changelog page.")
