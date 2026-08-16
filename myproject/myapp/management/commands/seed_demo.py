# Helper: fill the site with organised demo content using media already
# uploaded to the project's Cloudinary bucket. Idempotent — safe to re-run.
#
# Note on media fields: assigning FieldFile.name directly stores the Cloudinary
# public_id string without re-uploading, so every asset below must already
# exist in the bucket (verified via cloudinary.api.resources()).

from django.core.management.base import BaseCommand

from myapp.models import (
    HeroVideo,
    PortfolioCategory,
    PortfolioImage,
    PortfolioVideo,
    SiteSettings,
)


def _set_file(instance, field, public_id):
    """Store a Cloudinary public_id on a FileField without triggering an upload."""
    if public_id:
        getattr(instance, field).name = public_id


class Command(BaseCommand):
    help = "Seed organised demo content (hero, portfolio, team) from existing Cloudinary media."

    def handle(self, *args, **options):
        cat = {c.slug: c for c in PortfolioCategory.objects.all()}

        # ------------------------------------------------------- Hero videos
        hero_plan = {
            # main landscape hero on the homepage
            "main": dict(
                title="Wedding Cinematic Reel",
                video="media/hero/nqcrwnoo7krpmk7ofldw",
                poster="media/portfolio/posters/chamunda_studio_sutrapada-20260811-0001",
                orientation="landscape",
                is_featured=True,
                is_active=True,
                sort_order=0,
            ),
            # secondary portrait reels (kept ready in the admin)
            "alt-portrait-1": dict(
                title="Pre-Wedding Reel",
                video="media/hero/yiwray1h5ldau3jmvjxx",
                poster="media/portfolio/images/theweddingsofindiaofficial-20260813-0002",
                orientation="portrait",
                is_featured=False,
                is_active=True,
                sort_order=1,
            ),
            "alt-portrait-2": dict(
                title="Engagement Short",
                video="media/hero/eicfeyydysvs1arcsw1n",
                poster="media/portfolio/images/1000006118",
                orientation="portrait",
                is_featured=False,
                is_active=True,
                sort_order=2,
            ),
        }
        # Upgrade the existing "hro" test row to the featured landscape hero.
        existing = HeroVideo.objects.filter(sort_order=0).first() or HeroVideo.objects.first()
        if existing:
            upd = hero_plan.pop("main")
            for key, value in upd.items():
                if key == "video":
                    _set_file(existing, "video", value)
                elif key == "poster":
                    _set_file(existing, "poster", value)
                else:
                    setattr(existing, key, value)
            existing.save()
            self.stdout.write(f"Hero updated: #{existing.pk} {existing.title}")
        for key, data in hero_plan.items():
            video_pid = data.pop("video")
            poster_pid = data.pop("poster")
            obj = HeroVideo.objects.filter(video__endswith=video_pid).first()
            if not obj:
                obj = HeroVideo(title=data["title"])
            for field, value in data.items():
                setattr(obj, field, value)
            _set_file(obj, "video", video_pid)
            _set_file(obj, "poster", poster_pid)
            obj.save()
            self.stdout.write(f"Hero created: #{obj.pk} {obj.title}")
        self.stdout.write(f"Hero videos total: {HeroVideo.objects.count()}")

        # Homepage fallback image (shown behind/scaling until video loads).
        site = SiteSettings.load()
        _set_file(site, "hero_fallback", "media/portfolio/posters/chamunda_studio_sutrapada-20260811-0001")
        site.save()
        self.stdout.write("Site hero_fallback set.")

        # ---------------------------------------------------- Portfolio images
        IMAGES = [
            # (public_id, category_slug, title, alt, context)  — context: update existing by pk
            ("media/portfolio/images/chamunda_studio_sutrapada-20260812-0001_antlhz", "wedding", "Varmala at the Mandap", "Bride and groom exchanging varmala", 5),
            ("media/portfolio/images/theweddingsofindiaofficial-20260813-0001", "wedding", "Kalash & Decor Detail", "Traditional wedding decor", 6),
            ("media/portfolio/images/theweddingsofindiaofficial-20260813-0002", "pre-wedding", "Golden Hour Stroll", "Couple walking at sunset", 7),
            ("media/portfolio/images/theweddingsofindiaofficial-20260813-0005", "engagement", "Engagement Ring Shot", "Bride showing her ring", 8),
            ("media/portfolio/images/theweddingsofindiaofficial-20260813-0004", "pre-wedding", "Candid Laugh", "Candid laughing couple", 9),
            ("media/portfolio/images/img_1", "baby", "Little Star Session", "Baby studio portrait", 10),
            ("media/portfolio/images/1000006120", "couple", "Portrait by the Arch", "Elegant couple portrait", 11),
            ("media/portfolio/images/1000006119", "wedding", "Mehendi Details", "Mehendi close-up", 12),
            ("media/portfolio/images/1000006118", "wedding", "Bridal Portrait", "Bride in traditional wear", 13),
            # new demo rows (idempotent by public_id)
            ("media/portfolio/posters/chamunda_studio_sutrapada-20260811-0001", "wedding", "The Big Reveal", "Bride walking up the aisle", None),
            ("media/hero/Screenshot_20260705-220216_InstaPro_", "couple", "Vintage Frame", "Couple in a vintage styled shot", None),
            ("media/hero/chamunda_studio_sutrapada-20260812-0001", "maternity", "Expectant Glow", "Maternity portrait", None),
        ]
        sort = 0
        for public_id, cat_slug, title, alt, existing_pk in IMAGES:
            if existing_pk:
                obj = PortfolioImage.objects.filter(pk=existing_pk).first() or PortfolioImage()
            else:
                obj = PortfolioImage.objects.filter(image__endswith=public_id).first() or PortfolioImage()
            obj.title = title
            obj.alt_text = alt
            obj.category = cat.get(cat_slug)
            obj.is_active = True
            obj.sort_order = sort
            _set_file(obj, "image", public_id)
            obj.save()
            self.stdout.write(f"Portfolio image: #{obj.pk} {title}")
            sort += 1
        self.stdout.write(f"Portfolio images total: {PortfolioImage.objects.count()}")

        # ---------------------------------------------------- Portfolio videos
        VIDEOS = [
            # (public_id, poster_id, category_slug, title)
            ("media/portfolio/videos/pfqvfk9z8f1sbmazsifj", "media/portfolio/images/theweddingsofindiaofficial-20260813-0004", "pre-wedding", "Pre-Wedding Highlight"),
            ("media/portfolio/videos/lxavgnfqoerurves0sfd", "media/portfolio/images/theweddingsofindiaofficial-20260813-0005", "engagement", "Engagement Reel"),
            ("media/portfolio/videos/vuwz7lo5prre6tuangvq", "media/portfolio/images/1000006118", "wedding", "Wedding Cinematic"),
            ("media/hero/aw8sup9hmilq3hymmcjz", "media/portfolio/images/1000006119", "wedding", "Pheras Highlights"),
            ("media/hero/yiwray1h5ldau3jmvjxx", "media/portfolio/images/theweddingsofindiaofficial-20260813-0002", "pre-wedding", "Sunset Couple Film"),
            ("media/hero/lbxeolmq75bup1vcwlhd", "media/portfolio/images/1000006120", "couple", "Couple Short Film"),
            ("media/hero/e1yrzcqpnrpc9ogtpyyi", "media/portfolio/images/theweddingsofindiaofficial-20260813-0001", "engagement", "Engagement Moments"),
        ]
        for vid_pid, poster_pid, cat_slug, title in VIDEOS:
            obj = PortfolioVideo.objects.filter(video__endswith=vid_pid).first() or PortfolioVideo()
            obj.title = title
            obj.category = cat.get(cat_slug)
            obj.is_active = True
            obj.is_featured = cat_slug == "pre-wedding"
            _set_file(obj, "video", vid_pid)
            _set_file(obj, "poster", poster_pid)
            obj.save()
            self.stdout.write(f"Portfolio video: #{obj.pk} {title}")
        self.stdout.write(f"Portfolio videos total: {PortfolioVideo.objects.count()}")

        self.stdout.write(self.style.SUCCESS("\nDemo content seeded."))