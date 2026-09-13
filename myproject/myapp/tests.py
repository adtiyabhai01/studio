from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from datetime import date as cal_date

from .content import CONTENT_SECTIONS, TeamMemberForm
from .forms import EnquiryForm
from .models import Booking, Enquiry, PortfolioImage, TeamMember, ThemeSettings
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


def _tiny_gif(name="photo.gif"):
    # 1x1 transparent GIF — valid image bytes without Pillow dependency.
    return SimpleUploadedFile(
        name,
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
        b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
        b"\x00\x00\x02\x02D\x01\x00;",
        content_type="image/gif",
    )


class PortalBulkUploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("boss", "boss@example.com", "strongpass99")
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.user)
        self.url = reverse("main:portal_bulk_upload")

    def test_bulk_page_requires_staff(self):
        anon = Client(HTTP_HOST="localhost")
        resp = anon.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_bulk_page_renders(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Bulk Upload Photos")

    def test_ajax_single_upload_creates_photo(self):
        resp = self.client.post(
            self.url,
            {"image": _tiny_gif("shaadi-haldii.gif")},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(PortfolioImage.objects.count(), 1)
        self.assertIn("haldi", PortfolioImage.objects.first().title.lower())

    def test_classic_multifile_upload(self):
        resp = self.client.post(
            self.url,
            {"images": [_tiny_gif("a.gif"), _tiny_gif("b.gif")]},
        )
        self.assertRedirects(resp, reverse("main:portal_content_list", args=["portfolio-photos"]))
        self.assertEqual(PortfolioImage.objects.count(), 2)

    def test_list_shows_bulk_and_reorder_flags(self):
        PortfolioImage.objects.create(title="x", image=_tiny_gif("x.gif"))
        resp = self.client.get(reverse("main:portal_content_list", args=["portfolio-photos"]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["show_bulk"])
        self.assertTrue(resp.context["show_reorder"])
        self.assertTrue(CONTENT_SECTIONS["portfolio-photos"].sortable)
        self.assertFalse(CONTENT_SECTIONS["site-settings"].sortable)


class PortalReorderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("boss", "boss@example.com", "strongpass99")
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.user)
        self.a = PortfolioImage.objects.create(title="a", image=_tiny_gif("a.gif"), sort_order=0)
        self.b = PortfolioImage.objects.create(title="b", image=_tiny_gif("b.gif"), sort_order=1)
        self.c = PortfolioImage.objects.create(title="c", image=_tiny_gif("c.gif"), sort_order=2)
        self.url = reverse("main:portal_content_reorder", args=["portfolio-photos"])

    def test_reorder_persists(self):
        import json

        resp = self.client.post(
            self.url,
            data=json.dumps({"order": [self.c.pk, self.a.pk, self.b.pk]}),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(
            list(PortfolioImage.objects.order_by("sort_order").values_list("pk", flat=True)),
            [self.c.pk, self.a.pk, self.b.pk],
        )

    def test_reorder_rejects_empty(self):
        import json

        resp = self.client.post(
            self.url,
            data=json.dumps({"order": []}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


class PortalExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("boss", "boss@example.com", "strongpass99")
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.user)
        Enquiry.objects.create(name="Aarav Sharma", phone="9811111111", city="Jaipur", status="NEW")
        Enquiry.objects.create(name="Diya Patel", phone="9822222222", city="Udaipur", status="BOOKED")
        self.url = reverse("main:portal_enquiries_export")

    def test_export_requires_staff(self):
        anon = Client(HTTP_HOST="localhost")
        self.assertEqual(anon.get(self.url).status_code, 404)

    def test_export_csv_has_all_rows(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])
        self.assertIn("attachment", resp["Content-Disposition"])
        body = resp.content.decode("utf-8-sig")
        self.assertIn("Aarav Sharma", body)
        self.assertIn("Diya Patel", body)
        self.assertIn("9811111111", body)

    def test_export_filter_by_search_and_status(self):
        resp = self.client.get(self.url, {"q": "diya"})
        body = resp.content.decode("utf-8-sig")
        self.assertNotIn("Aarav Sharma", body)
        self.assertIn("Diya Patel", body)
        resp = self.client.get(self.url, {"status": "BOOKED"})
        body = resp.content.decode("utf-8-sig")
        self.assertNotIn("Aarav Sharma", body)
        self.assertIn("Diya Patel", body)


class CuratedFontsTests(TestCase):
    def test_six_headings_six_body(self):
        from .models import BODY_FONTS, HEADING_FONTS

        self.assertEqual(len(HEADING_FONTS), 6)
        self.assertEqual(len(BODY_FONTS), 6)
        self.assertEqual(HEADING_FONTS[0][1], "Playfair Display")
        self.assertEqual(BODY_FONTS[0][1], "Manrope")

    def test_presets_use_valid_curated_fonts(self):
        from .models import BODY_FONTS, HEADING_FONTS, THEME_PRESETS

        heading_stacks = {stack for stack, _label in HEADING_FONTS}
        body_stacks = {stack for stack, _label in BODY_FONTS}
        for preset in THEME_PRESETS:
            self.assertIn(preset["heading"], heading_stacks, preset["key"])
            self.assertIn(preset["body"], body_stacks, preset["key"])

    def test_retired_map_targets_are_curated(self):
        from .models import BODY_FONTS, HEADING_FONTS, RETIRED_FONT_MAP

        valid = {stack for stack, _label in HEADING_FONTS + BODY_FONTS}
        self.assertTrue(len(RETIRED_FONT_MAP) >= 15)
        for old, new in RETIRED_FONT_MAP.items():
            self.assertIn(new, valid)
            self.assertNotIn(old, valid)


class AvailabilityCalendarTests(TestCase):
    def test_past_booking_rejected(self):
        yesterday = timezone.localdate() - timezone.timedelta(days=1)
        with self.assertRaises(ValidationError):
            Booking.objects.create(date=yesterday, status="BOOKED")

    def test_today_and_future_booking_allowed(self):
        today = timezone.localdate()
        Booking.objects.create(date=today, status="BOOKED", client_name="Aarav")
        Booking.objects.create(
            date=today + timezone.timedelta(days=30), status="BLOCKED", notes="Diwali"
        )
        self.assertEqual(Booking.objects.count(), 2)

    def test_availability_page_marks_booked(self):
        today = timezone.localdate()
        target = today + timezone.timedelta(days=5)
        Booking.objects.create(date=target, status="BOOKED", client_name="Diya")
        client = Client(HTTP_HOST="localhost")
        resp = client.get(f"/availability/?y={target.year}&m={target.month}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(target, resp.context["booked"])
        self.assertEqual(resp.context["booked"][target], "BOOKED")
        self.assertContains(resp, "is-booked")

    def test_availability_clamps_past_month(self):
        today = timezone.localdate()
        client = Client(HTTP_HOST="localhost")
        resp = client.get("/availability/?y=2000&m=1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["wanted"], cal_date(today.year, today.month, 1))

    def test_enquiry_form_rejects_past_date(self):
        yesterday = timezone.localdate() - timezone.timedelta(days=1)
        form = EnquiryForm(
            data={
                "name": "A",
                "phone": "9811111111",
                "budget": "under_25000",
                "event_date": yesterday.isoformat(),
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("event_date", form.errors)

    def test_enquiry_form_accepts_future_date(self):
        future = timezone.localdate() + timezone.timedelta(days=10)
        form = EnquiryForm(
            data={
                "name": "A",
                "phone": "9811111111",
                "budget": "under_25000",
                "event_date": future.isoformat(),
            }
        )
        self.assertTrue(form.is_valid())

    def test_contact_prefills_future_date_only(self):
        client = Client(HTTP_HOST="localhost")
        future = (timezone.localdate() + timezone.timedelta(days=7)).isoformat()
        past = (timezone.localdate() - timezone.timedelta(days=7)).isoformat()
        resp = client.get(f"/contact/?date={future}")
        self.assertEqual(resp.context["form"].initial.get("event_date"), future)
        resp = client.get(f"/contact/?date={past}")
        self.assertNotIn("event_date", resp.context["form"].initial)

    def test_bookings_portal_requires_staff(self):
        anon = Client(HTTP_HOST="localhost")
        self.assertEqual(
            anon.get(reverse("main:portal_content_list", args=["bookings"])).status_code, 404
        )
        user = User.objects.create_superuser("boss", "boss@example.com", "strongpass99")
        staff = Client(HTTP_HOST="localhost")
        staff.force_login(user)
        resp = staff.get(reverse("main:portal_content_list", args=["bookings"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Bookings")