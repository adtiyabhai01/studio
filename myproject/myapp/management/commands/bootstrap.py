import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from myapp.models import (
    City,
    Offer,
    Package,
    PortfolioCategory,
    Service,
    SiteSettings,
    Testimonial,
)

USERNAME = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
EMAIL = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@studio.local")
PASSWORD = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "0000")


def _service(slug):
    return Service.objects.filter(slug=slug).first()


class Command(BaseCommand):
    help = "Create an admin user and seed starter content (helper only)."

    def handle(self, *args, **options):
        self.stdout.write("Booting management workspace\u2026")

        User = get_user_model()
        if not User.objects.filter(username=USERNAME).exists():
            User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{USERNAME}' created (password: {PASSWORD})."))
        else:
            self.stdout.write(f"Superuser '{USERNAME}' already exists.")

        if not City.objects.exists():
            cities = [
                ("Delhi", True), ("Mumbai", True), ("Bengaluru", True),
                ("Hyderabad", True), ("Pune", True), ("Jaipur", True),
                ("Kolkata", False), ("Ahmedabad", False), ("Lucknow", False),
                ("Chandigarh", False), ("Udaipur", False), ("Goa", False),
                ("Indore", False), ("Nagpur", False), ("Surat", False),
            ]
            for idx, (name, featured) in enumerate(cities):
                City.objects.create(name=name, is_featured=featured, sort_order=idx)
            self.stdout.write("Cities seeded.")

        services_map = {
            "wedding": (
                "Wedding Photography",
                "wedding",
                "Cinematic wedding photography for every budget.",
                "Two full days of storytelling \u2014 emotion, light and every once-in-a-lifetime detail, crafted into a gallery and film your family will watch forever.",
            ),
            "wedding-videography": (
                "Wedding Videography",
                "wedding",
                "Cinematic films with soul.",
                "A premium cinematic film that compresses every laugh, tear and dance into an edit you will relive for a lifetime.",
            ),
            "pre-wedding": (
                "Pre-Wedding Shoot",
                "prewedding",
                "Your love story, shot like a movie.",
                "Breathtaking locations, golden hour light and candid moments \u2014 a pre-wedding experience designed around the two of you.",
            ),
            "engagement": (
                "Engagement & Couple",
                "engagement",
                "Celebrate the promise.",
                "Elegant engagement and couple shoots that freeze the excitement of starting forever together.",
            ),
            "couple": (
                "Couple Shoot",
                "couple",
                "Just the two of you.",
                "A relaxed, candid couple session anywhere in your city.",
            ),
            "maternity": (
                "Maternity",
                "maternity",
                "The glow of beginnings.",
                "Graceful, emotional maternity portraits that celebrate this once-in-a-lifetime chapter.",
            ),
            "baby": (
                "Baby Shoot",
                "baby",
                "Tiny toes, giant moments.",
                "Safe, playful photography of your little one's first months \u2014 every gummy smile and tiny yawn, preserved forever.",
            ),
        }
        for slug, (name, icon, tagline, desc) in services_map.items():
            Service.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "icon_key": icon,
                    "tagline": tagline,
                    "short_description": tagline,
                    "description": desc,
                    "is_featured": slug in ("wedding", "pre-wedding", "maternity", "baby"),
                },
            )
        self.stdout.write(f"Services ({Service.objects.count()}) seeded.")

        category_map = {
            "wedding": "Wedding",
            "pre-wedding": "Pre-Wedding",
            "engagement": "Engagement",
            "couple": "Couple",
            "baby": "Baby",
            "maternity": "Maternity",
        }
        for slug, name in category_map.items():
            if not PortfolioCategory.objects.filter(slug=slug).exists():
                PortfolioCategory.objects.create(name=name, slug=slug)
        self.stdout.write("Portfolio categories seeded.")

        packages = [
            dict(
                name="1. Wedding \u2014 Affordable",
                category="affordable",
                price=25000,
                old_price=None,
                description="Beautiful wedding coverage for budget celebrations, without compromising on heart.",
                photographers=1,
                videographers=0,
                hours=8,
                edited_photos=300,
                reels=1,
                cinematic_film=True,
                album=True,
                drone=False,
                services=["wedding"],
            ),
            dict(
                name="2. Wedding \u2014 Classic",
                category="classic",
                price=45000,
                old_price=52000,
                description="A balanced mix of photography and a short cinematic film.",
                photographers=1,
                videographers=1,
                hours=10,
                edited_photos=450,
                reels=2,
                cinematic_film=True,
                album=True,
                drone=False,
                services=["wedding", "pre-wedding"],
            ),
            dict(
                name="3. Wedding \u2014 Premium",
                category="premium",
                price=75000,
                old_price=88000,
                description="Two shooters on your big day plus a full premium film.",
                photographers=2,
                videographers=1,
                hours=12,
                edited_photos=800,
                reels=3,
                cinematic_film=True,
                album=True,
                drone=True,
                full_day_coverage=True,
                services=["wedding", "engagement", "maternity"],
            ),
            dict(
                name="4. Wedding \u2014 Luxury",
                category="luxury",
                price=125000,
                old_price=140000,
                description="Our signature experience \u2014 destination ready, fully dedicated crew.",
                photographers=2,
                videographers=2,
                hours=16,
                edited_photos=1200,
                reels=5,
                cinematic_film=True,
                album=True,
                drone=True,
                full_day_coverage=True,
                same_day_edit=True,
                services=["wedding", "pre-wedding", "engagement", "baby", "maternity"],
            ),
            dict(
                name="Pre-Wedding Film & Still",
                category="premium",
                price=35000,
                old_price=None,
                description="A cinematic couple of film plus a styled photo gallery.",
                photographers=1,
                videographers=1,
                hours=6,
                edited_photos=200,
                reels=2,
                cinematic_film=True,
                album=False,
                drone=True,
                services=["pre-wedding", "engagement"],
            ),
            dict(
                name="Maternity Mini",
                category="classic",
                price=12000,
                old_price=15000,
                description="A warm maternity session \u2014 two outfit changes, 40 edited portraits.",
                photographers=1,
                videographers=0,
                hours=2,
                edited_photos=40,
                reels=0,
                cinematic_film=False,
                album=False,
                drone=False,
                services=["maternity"],
            ),
            dict(
                name="Baby Milestone",
                category="affordable",
                price=8999,
                old_price=11000,
                description="One studio session for your little star \u2014 newborn, 3-month, 6-month or first birthday.",
                photographers=1,
                videographers=0,
                hours=2,
                edited_photos=35,
                reels=1,
                cinematic_film=False,
                album=False,
                drone=False,
                services=["baby"],
            ),
        ]
        for data in packages:
            services = data.pop("services", [])
            name = data.pop("name")
            pkg, _ = Package.objects.update_or_create(name=name, defaults=data)
            if services:
                pkg.services.set(Service.objects.filter(slug__in=services))
        self.stdout.write(f"Packages ({Package.objects.count()}) seeded.")

        offers = [
            {
                "title": "Baby Shoot + Engagement Shoot",
                "slug": "baby-engagement-combo",
                "description": "Celebrate two milestones with one beautiful package \u2014 a studio baby session and a candid engagement shoot, together at one wonderful price.",
                "original_price": 25000,
                "offer_price": 18999,
                "is_featured": True,
                "services": ["baby", "engagement"],
                "included": [
                    "Baby shoot studio session",
                    "Engagement / couple shoot",
                    "All edited photos",
                    "One cinematic reel",
                    "Framed 8x12 print each",
                ],
            },
            {
                "title": "Classic Wedding Combo",
                "slug": "classic-wedding-combo",
                "description": "Photography + a short cinematic film + 10 curated prints \u2014 the complete classic experience.",
                "original_price": 52000,
                "offer_price": 45000,
                "is_featured": True,
                "services": ["wedding"],
                "included": [
                    "Full-day photography",
                    "Short cinematic film",
                    "Web gallery",
                    "10 framed prints",
                    "Highlights reel",
                ],
            },
        ]
        for o in offers:
            services = o.pop("services", [])
            included = o.pop("included", [])
            defaults = dict(o)
            defaults["included_services"] = "\n".join(included)
            offer, _ = Offer.objects.update_or_create(slug=o["slug"], defaults=defaults)
            if services:
                offer.services.set(Service.objects.filter(slug__in=services))
        self.stdout.write(f"Offers ({Offer.objects.count()}) seeded.")

        if not Testimonial.objects.exists():
            Testimonial.objects.create(
                client_name="Aarav & Meera",
                event_type="Wedding",
                city="Jaipur",
                rating=5,
                review="They captured the soul of our wedding. The highlight film makes us cry every single time. Worth every rupee.",
                is_featured=True,
            )
            Testimonial.objects.create(
                client_name="Rohit & Ananya",
                event_type="Pre-Wedding",
                city="Goa",
                rating=5,
                review="The pre-wedding shoot in Goa was like a movie set. The team made us feel comfortable and the photos are artworks.",
                is_featured=True,
            )
            Testimonial.objects.create(
                client_name="Neha & Kabir",
                event_type="Engagement",
                city="Mumbai",
                rating=5,
                review="Friendly team, gorgeous frames, and the reel they made for us went viral among our friends!",
                is_featured=True,
            )
            Testimonial.objects.create(
                client_name="Prisha Sharma",
                event_type="Maternity",
                city="Pune",
                rating=5,
                review="So gentle and elegant. My maternity portraits are the most beautiful memory of my pregnancy.",
                is_featured=True,
            )
            Testimonial.objects.create(
                client_name="Vikram & Sneha",
                event_type="Baby Shoot",
                city="Bengaluru",
                rating=5,
                review="They caught all those tiny expressions at my son's first birthday. His first year, beautifully preserved.",
                is_featured=False,
            )
        self.stdout.write(f"Testimonials ({Testimonial.objects.count()}) seeded.")

        SiteSettings.load()
        self.stdout.write("Site settings ready.")

        self.stdout.write(self.style.SUCCESS("\nAll done."))
        self.stdout.write("Admin login: /admin/  \u00b7  user: %s   pass: %s\n" % (USERNAME, PASSWORD))