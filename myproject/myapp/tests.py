from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .content import TeamMemberForm
from .models import Enquiry, TeamMember, ThemeSettings
from .views import THEME_COLOR_KEYS


class TeamMemberDeveloperTests(TestCase):
    def setUp(self):
        self.dev = TeamMember.objects.create(name="Ada Dev", role="Developer", is_developer=True)

    def test_first_developer_allowed(self):
        self.assertTrue(TeamMember.objects.get(pk=self.dev.pk).is_developer)

    def test_second_developer_rejected_on_save(self):
        with self.assertRaises(ValidationError):
            TeamMember.objects.create(name="Bob", role="Dev", is_developer=True)

    def test_second_developer_rejected_by_portal_form(self):
        form = TeamMemberForm(
            data={
                "name": "Bob",
                "role": "Dev",
                "is_developer": True,
                "is_active": True,
                "sort_order": 0,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("is_developer", form.errors)

    def test_database_constraint_blocks_second_developer(self):
        TeamMember.objects.filter(pk=self.dev.pk).update(is_developer=False)
        TeamMember.objects.create(name="Bob", role="Dev", is_developer=True)
        with self.assertRaises(ValidationError):
            TeamMember.objects.create(name="Carol", role="Dev", is_developer=True)

    def test_unmark_existing_allows_new_developer(self):
        self.dev.is_developer = False
        self.dev.save()
        TeamMember.objects.create(name="Bob", role="Dev", is_developer=True)
        self.assertEqual(TeamMember.objects.filter(is_developer=True).count(), 1)

    def test_existing_developer_can_be_edited(self):
        self.dev.name = "Ada Dev Updated"
        self.dev.save()
        self.assertEqual(TeamMember.objects.get(pk=self.dev.pk).name, "Ada Dev Updated")

    def test_developer_sorts_first(self):
        TeamMember.objects.create(name="Zoe", role="Photographer", sort_order=1)
        self.assertTrue(TeamMember.objects.first().is_developer)


class AboutPageTeamTests(TestCase):
    def test_about_page_renders_developer_and_members(self):
        dev = TeamMember.objects.create(name="Ada Dev", role="Developer", is_developer=True)
        member = TeamMember.objects.create(name="Zoe", role="Photographer")
        client = Client(HTTP_HOST="localhost")
        resp = client.get("/about/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "team-dev")
        self.assertContains(resp, "Ada Dev")
        self.assertContains(resp, "team-photo")
        self.assertContains(resp, "Zoe")
        self.assertEqual(resp.context["team_developer"].pk, dev.pk)
        self.assertEqual([m.pk for m in resp.context["team"]], [member.pk])


class AdminPortalTabPreservationTests(TestCase):
    """Actions in the admin portal must redirect back to the tab the user
    was on (not reset to the default 'enquiries' tab)."""

    def setUp(self):
        self.user = User.objects.create_superuser("boss", "boss@example.com", "strongpass99")
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.user)
        self.url = reverse("main:admin_portal")

    def test_maintenance_toggle_redirects_to_site_tab(self):
        resp = self.client.post(self.url, {"portal_action": "maintenance", "tab": "site"})
        self.assertRedirects(resp, self.url + "?tab=site")

    def test_theme_save_redirects_to_theme_tab(self):
        theme = ThemeSettings.load()
        data = {"portal_action": "theme", "tab": "theme", "is_custom": "on"}
        for key in THEME_COLOR_KEYS:
            data[key] = getattr(theme, key).lower()
        data["container_width"] = str(theme.container_width)
        data["heading_font"] = theme.heading_font
        data["body_font"] = theme.body_font
        resp = self.client.post(self.url, data)
        self.assertRedirects(resp, self.url + "?tab=theme")

    def test_theme_reset_redirects_to_theme_tab(self):
        resp = self.client.post(self.url, {"portal_action": "theme", "tab": "theme", "reset_theme": "1"})
        self.assertRedirects(resp, self.url + "?tab=theme")

    def test_status_update_redirects_to_enquiries_tab(self):
        enquiry = Enquiry.objects.create(name="Neha", phone="9876500000", status="NEW")
        resp = self.client.post(
            self.url,
            {"portal_action": "status", "enquiry_id": str(enquiry.pk), "status": "CONTACTED", "tab": "enquiries"},
        )
        self.assertRedirects(resp, self.url + "?tab=enquiries")

    def test_missing_tab_falls_back_to_plain_redirect(self):
        resp = self.client.post(self.url, {"portal_action": "maintenance"})
        self.assertRedirects(resp, self.url)