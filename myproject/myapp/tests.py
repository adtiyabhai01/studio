from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from .content import TeamMemberForm
from .models import TeamMember


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