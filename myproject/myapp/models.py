from django.db import models
from django.utils import timezone

from cloudinary_storage.storage import VideoMediaCloudinaryStorage

# ---------------------------------------------------------------------------
# Choices / constants
# ---------------------------------------------------------------------------

PACKAGE_CATEGORIES = [
    ("affordable", "Affordable"),
    ("classic", "Classic"),
    ("premium", "Premium"),
    ("luxury", "Luxury"),
]

BUDGET_CHOICES = [
    ("under_25000", "Under \u20b925,000"),
    ("25000_50000", "\u20b925,000 \u2013 \u20b950,000"),
    ("50000_100000", "\u20b950,000 \u2013 \u20b91,00,000"),
    ("100000_plus", "\u20b91,00,000+"),
    ("luxury", "Luxury / Custom"),
]

ENQUIRY_STATUS = [
    ("NEW", "New"),
    ("CONTACTED", "Contacted"),
    ("FOLLOW_UP", "Follow Up"),
    ("BOOKED", "Booked"),
    ("COMPLETED", "Completed"),
    ("CLOSED", "Closed"),
]

RATING_CHOICES = [(i, i) for i in range(1, 6)]


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Site settings (singleton)
# ---------------------------------------------------------------------------


class SiteSettings(TimeStampedModel):
    brand_name = models.CharField(max_length=120, default="Chamunda Studio")
    logo = models.ImageField(
        upload_to="site/", blank=True, null=True, help_text="Site logo shown in the header & footer."
    )
    tagline = models.CharField(
        max_length=200,
        blank=True,
        default="Photography & Cinematography",
    )
    site_description = models.TextField(
        blank=True,
        default="Premium photography & videography studio crafting timeless wedding, "
        "pre-wedding, engagement, maternity and baby stories across every city.",
    )
    phones = models.CharField(
        max_length=200, blank=True, default="+91 98765 43210", help_text="Comma separated numbers."
    )
    whatsapp_number = models.CharField(
        max_length=20, default="919876543210", help_text="Include country code, digits only."
    )
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    youtube = models.URLField(blank=True)

    home_hero_title = models.CharField(
        max_length=200, default="Every love story is a film waiting to be made."
    )
    home_hero_subtitle = models.CharField(
        max_length=300,
        default="Timeless wedding, pre-wedding, maternity and baby stories \u2014 shot across every city.",
    )
    years_experience = models.PositiveIntegerField(default=8)
    events_shot = models.PositiveIntegerField(default=600, verbose_name="Events shot")
    happy_clients = models.PositiveIntegerField(default=900)
    hero_fallback = models.ImageField(
        upload_to="site/", blank=True, null=True, help_text="Fallback hero image when no video is available."
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.brand_name

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def phone_list(self):
        return [p.strip() for p in self.phones.split(",") if p.strip()]

    def whatsapp_link(self, message=None):
        base = f"https://wa.me/{self.whatsapp_number}"
        if message:
            base += f"?text={message}"
        return base


HEADING_FONTS = [
    ("'Playfair Display', Georgia, serif", "Playfair Display"),
    ("'Cormorant Garamond', Georgia, serif", "Cormorant Garamond"),
    ("'Marcellus', Georgia, serif", "Marcellus"),
    ("'Libre Baskerville', Georgia, serif", "Libre Baskerville"),
    ("'EB Garamond', Georgia, serif", "EB Garamond"),
]

BODY_FONTS = [
    ("Manrope, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", "Manrope"),
    ("Poppins, -apple-system, BlinkMacSystemFont, sans-serif", "Poppins"),
    ("Inter, -apple-system, BlinkMacSystemFont, sans-serif", "Inter"),
    ("Jost, -apple-system, BlinkMacSystemFont, sans-serif", "Jost"),
    ("'Nunito Sans', -apple-system, BlinkMacSystemFont, sans-serif", "Nunito Sans"),
]

DEFAULT_FONT_STACKS = {
    "heading": HEADING_FONTS[0][0],
    "body": BODY_FONTS[0][0],
}


class ThemeSettings(TimeStampedModel):
    """Singleton controlling the live CSS variables used by the public theme."""

    is_custom = models.BooleanField(
        default=True, help_text="Apply the custom theme below. Uncheck to use the default design."
    )

    background = models.CharField(max_length=9, default="#0f0d0c", help_text="Page background")
    background_secondary = models.CharField(max_length=9, default="#141211", help_text="Card / section background")
    ink = models.CharField(max_length=9, default="#1b1816", help_text="Darkest text on light surfaces")
    ink_secondary = models.CharField(max_length=9, default="#221e1a")
    ivory = models.CharField(max_length=9, default="#f4eee2", help_text="Main light text / surface")
    ivory_secondary = models.CharField(max_length=9, default="#ece3d2")
    cream = models.CharField(max_length=9, default="#faf6ef", help_text="Light page backgrounds")
    primary = models.CharField(max_length=9, default="#b28a54", help_text="Brand accent (gold)")
    primary_strong = models.CharField(max_length=9, default="#d9bd8b", help_text="Bright accent (hover)")
    primary_deep = models.CharField(max_length=9, default="#8f6a3f", help_text="Deep accent")
    muted = models.CharField(max_length=9, default="#b7a98f", help_text="Muted text")
    muted_secondary = models.CharField(max_length=9, default="#7c7161", help_text="Fainter text")

    heading_font = models.CharField(max_length=200, choices=HEADING_FONTS, default=HEADING_FONTS[0][0])
    body_font = models.CharField(max_length=200, choices=BODY_FONTS, default=BODY_FONTS[0][0])
    container_width = models.PositiveIntegerField(default=1180, help_text="Max content width in px")

    class Meta:
        verbose_name = "Theme Settings"
        verbose_name_plural = "Theme Settings"

    def __str__(self):
        return "Theme Settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ---------------------------------------------------------------------------
# Ready-made theme palettes (one-click presets for the admin portal)
# ---------------------------------------------------------------------------

THEME_PRESETS = [
    {
        "key": "noir_gold",
        "name": "Noir & Gold",
        "description": "Classic studio black with warm gold accents.",
        "heading": HEADING_FONTS[0][0],
        "body": BODY_FONTS[0][0],
        "colors": {
            "background": "#0f0d0c",
            "background_secondary": "#141211",
            "ink": "#1b1816",
            "ink_secondary": "#221e1a",
            "ivory": "#f4eee2",
            "ivory_secondary": "#ece3d2",
            "cream": "#faf6ef",
            "primary": "#b28a54",
            "primary_strong": "#d9bd8b",
            "primary_deep": "#8f6a3f",
            "muted": "#b7a98f",
            "muted_secondary": "#7c7161",
        },
    },
    {
        "key": "midnight_champagne",
        "name": "Midnight & Champagne",
        "description": "Deep navy-black with elegant champagne highlights.",
        "heading": HEADING_FONTS[1][0],
        "body": BODY_FONTS[3][0],
        "colors": {
            "background": "#0b1017",
            "background_secondary": "#10161f",
            "ink": "#1a2029",
            "ink_secondary": "#232b38",
            "ivory": "#f1ede2",
            "ivory_secondary": "#e6e0d2",
            "cream": "#f8f5ec",
            "primary": "#c9a87c",
            "primary_strong": "#e7d4b2",
            "primary_deep": "#9d7e54",
            "muted": "#aab6c4",
            "muted_secondary": "#7d8894",
        },
    },
    {
        "key": "forest_brass",
        "name": "Forest & Brass",
        "description": "Dark botanical green with aged brass accents.",
        "heading": HEADING_FONTS[2][0],
        "body": BODY_FONTS[3][0],
        "colors": {
            "background": "#0d120e",
            "background_secondary": "#121912",
            "ink": "#1c241d",
            "ink_secondary": "#263028",
            "ivory": "#efe9db",
            "ivory_secondary": "#e6dfcf",
            "cream": "#f7f3e9",
            "primary": "#b8945c",
            "primary_strong": "#d9bf85",
            "primary_deep": "#8f7142",
            "muted": "#a8b1a0",
            "muted_secondary": "#707b6d",
        },
    },
    {
        "key": "bordeaux_rosegold",
        "name": "Bordeaux & Rose Gold",
        "description": "Warm plum-black with soft rose gold glow.",
        "heading": HEADING_FONTS[0][0],
        "body": BODY_FONTS[0][0],
        "colors": {
            "background": "#140e0e",
            "background_secondary": "#1a1212",
            "ink": "#251b1b",
            "ink_secondary": "#302222",
            "ivory": "#f2e6e0",
            "ivory_secondary": "#e9d9d1",
            "cream": "#faf2ec",
            "primary": "#d09a86",
            "primary_strong": "#eebdab",
            "primary_deep": "#a9715c",
            "muted": "#c2a49a",
            "muted_secondary": "#8b6b61",
        },
    },
    {
        "key": "slate_silver",
        "name": "Slate & Silver",
        "description": "Editorial charcoal with cool silver accents.",
        "heading": HEADING_FONTS[3][0],
        "body": BODY_FONTS[2][0],
        "colors": {
            "background": "#121315",
            "background_secondary": "#181a1c",
            "ink": "#212327",
            "ink_secondary": "#2b2e33",
            "ivory": "#edeff1",
            "ivory_secondary": "#e2e5e8",
            "cream": "#f6f7f8",
            "primary": "#aeb6bd",
            "primary_strong": "#d4d9de",
            "primary_deep": "#7f8891",
            "muted": "#bac1c8",
            "muted_secondary": "#7d848c",
        },
    },
    {
        "key": "sapphire_platinum",
        "name": "Sapphire & Platinum",
        "description": "Midnight blue-black with platinum steel accents.",
        "heading": HEADING_FONTS[1][0],
        "body": BODY_FONTS[2][0],
        "colors": {
            "background": "#0a0e16",
            "background_secondary": "#101621",
            "ink": "#1a2130",
            "ink_secondary": "#232d40",
            "ivory": "#eef1f6",
            "ivory_secondary": "#e3e8f0",
            "cream": "#f7f9fc",
            "primary": "#a8b6d4",
            "primary_strong": "#cdd8ee",
            "primary_deep": "#7d8eb0",
            "muted": "#aab4c6",
            "muted_secondary": "#7d8798",
        },
    },
    {
        "key": "ivory_copper",
        "name": "Ivory & Copper",
        "description": "Bright, airy ivory theme with warm copper accents.",
        "heading": HEADING_FONTS[0][0],
        "body": BODY_FONTS[1][0],
        "colors": {
            "background": "#f6f0e5",
            "background_secondary": "#efe7d8",
            "ink": "#2b2722",
            "ink_secondary": "#3a352e",
            "ivory": "#3d362c",
            "ivory_secondary": "#4a4338",
            "cream": "#fdfaf4",
            "primary": "#c07a4d",
            "primary_strong": "#d99560",
            "primary_deep": "#9c5c36",
            "muted": "#8a8070",
            "muted_secondary": "#6f6558",
        },
    },
]


class City(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Cities"

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

SERVICE_TEMPLATE_KEYS = ["wedding", "pre-wedding", "engagement", "baby", "maternity"]


class Service(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    icon_key = models.CharField(
        max_length=60, blank=True, help_text="e.g. wedding, prewedding, engagement, couple, maternity, baby"
    )
    tagline = models.CharField(max_length=180, blank=True)
    short_description = models.CharField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="services/", blank=True, null=True)
    video = models.FileField(upload_to="services/", blank=True, null=True, storage=VideoMediaCloudinaryStorage())
    video_poster = models.ImageField(upload_to="services/posters/", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.slug in SERVICE_TYPES:
            return f"/services/{self.slug}/"
        redirect_map = {
            "wedding-videography": "/services/wedding/",
            "couple": "/services/engagement/",
        }
        if self.slug in redirect_map:
            return redirect_map[self.slug]
        return "/services/"


SERVICE_TYPES = {
    "wedding": "wedding",
    "pre-wedding": "prewedding",
    "engagement": "engagement",
    "baby": "baby",
    "maternity": "maternity",
}


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------


class PortfolioCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Portfolio categories"

    def __str__(self):
        return self.name


class PortfolioImage(models.Model):
    category = models.ForeignKey(
        PortfolioCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="images"
    )
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="portfolio/images/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title or f"Image #{self.pk}"

    def get_alt(self):
        return self.alt_text or self.title or (self.category.name if self.category else "Portfolio photo")


class PortfolioVideo(models.Model):
    category = models.ForeignKey(
        PortfolioCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="videos"
    )
    title = models.CharField(max_length=200, blank=True)
    video = models.FileField(upload_to="portfolio/videos/", blank=True, null=True, storage=VideoMediaCloudinaryStorage())
    youtube_url = models.URLField(blank=True, help_text="YouTube embed URL if not uploading a video file.")
    poster = models.ImageField(upload_to="portfolio/posters/", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title or f"Video #{self.pk}"

    def embed_id(self):
        if not self.youtube_url:
            return ""
        url = self.youtube_url.strip()
        for marker in ("youtu.be/", "embed/", "watch?v=", "shorts/"):
            if marker in url:
                return url.split(marker)[-1].split("?")[0].split("/")[0]
        return url


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------


class Package(TimeStampedModel):
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=PACKAGE_CATEGORIES, default="classic", db_index=True)
    services = models.ManyToManyField(
        Service, related_name="packages", blank=True, help_text="Show this package on these service pages."
    )
    price = models.DecimalField(max_digits=12, decimal_places=0)
    old_price = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="packages/", blank=True, null=True)

    photographers = models.PositiveIntegerField(default=1)
    videographers = models.PositiveIntegerField(default=0)
    hours = models.PositiveIntegerField(default=8)
    edited_photos = models.PositiveIntegerField(default=0)
    reels = models.PositiveIntegerField(default=0, help_text="Set 0 to hide this row.")
    cinematic_film = models.BooleanField(default=False)
    album = models.BooleanField(default=False)
    drone = models.BooleanField(default=False)
    full_day_coverage = models.BooleanField(default=False)
    same_day_edit = models.BooleanField(default=False)
    deliverables = models.TextField(blank=True)

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int((float(self.old_price - self.price) / float(self.old_price)) * 100)
        return 0


class PackageFeature(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="features")
    label = models.CharField(max_length=140)
    value = models.CharField(max_length=140, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.label} \u2014 {self.value or ''}"


# ---------------------------------------------------------------------------
# Offers
# ---------------------------------------------------------------------------


class Offer(TimeStampedModel):
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    services = models.ManyToManyField(Service, related_name="offers", blank=True)
    included_services = models.TextField(
        blank=True, help_text="One item per line. Shown as a checklist on the offer card."
    )
    original_price = models.DecimalField(max_digits=12, decimal_places=0)
    offer_price = models.DecimalField(max_digits=12, decimal_places=0)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to="offers/", blank=True, null=True)
    video = models.FileField(upload_to="offers/videos/", blank=True, null=True, storage=VideoMediaCloudinaryStorage())
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title

    @property
    def is_current(self):
        today = timezone.localdate()
        if not self.is_active:
            return False
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True

    def included_list(self):
        return [line.strip() for line in self.included_services.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Testimonials
# ---------------------------------------------------------------------------


class Testimonial(models.Model):
    client_name = models.CharField(max_length=120)
    client_photo = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    event_type = models.CharField(max_length=120, blank=True, default="Wedding")
    city = models.CharField(max_length=120, blank=True)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    review = models.TextField()
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.client_name

    def rating_stars(self):
        return self.rating


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------


class TeamMember(TimeStampedModel):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(upload_to="team/", blank=True, null=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Enquiry
# ---------------------------------------------------------------------------


class Enquiry(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="enquiries"
    )
    event_date = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=120, blank=True)
    budget = models.CharField(max_length=30, choices=BUDGET_CHOICES, default="under_25000")
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ENQUIRY_STATUS, default="NEW", db_index=True)
    notes = models.TextField(blank=True, help_text="Internal notes for the studio.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Enquiries"

    def __str__(self):
        return f"{self.name} \u2013 {self.phone}"

    def get_budget_display(self):
        return dict(BUDGET_CHOICES).get(self.budget, self.budget)


# ---------------------------------------------------------------------------
# Hero videos
# ---------------------------------------------------------------------------


class HeroVideo(models.Model):
    title = models.CharField(max_length=120, blank=True)
    video = models.FileField(upload_to="hero/", blank=True, null=True, help_text="MP4 recommended.", storage=VideoMediaCloudinaryStorage())
    poster = models.ImageField(upload_to="hero/", blank=True, null=True, help_text="Shown until video loads.")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name_plural = "Hero videos"

    def __str__(self):
        return self.title or f"Hero video #{self.pk}"