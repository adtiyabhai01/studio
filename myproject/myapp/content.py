"""
Frontend content manager for the admin portal.

Replaces the embedded Django admin iframe with a branded, user-friendly UI for
viewing, adding, editing and deleting content.  Each manageable model gets a
ModelForm (portal-styled widgets) plus a ContentSection describing how its
records are listed, searched and paginated inside the portal.
"""

from django import forms
from django.conf import settings
from django.utils.html import format_html
from django.utils.text import slugify

from .models import (
    City,
    HeroVideo,
    Offer,
    Package,
    PackageFeature,
    PortfolioCategory,
    PortfolioImage,
    PortfolioVideo,
    Service,
    SiteSettings,
    TeamMember,
    Testimonial,
)


class PortalModelForm(forms.ModelForm):
    """Base form that applies the portal's .field styling to every widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "slug":
                # Slug is auto-generated from the name/title when left blank.
                field.required = False
            # On an empty (Add) form, pre-fill fields that carry model defaults
            # (e.g. is_active, rating, sort_order) so they're visible and optional.
            model_field = None
            if not self.instance.pk and hasattr(self._meta, "model"):
                try:
                    model_field = self._meta.model._meta.get_field(name)
                except Exception:
                    model_field = None
            if (
                model_field
                and name not in self.data
                and not field.initial
                and model_field.has_default()
            ):
                field.initial = model_field.get_default()
                field.required = False
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                css = "field-check-group"
            elif isinstance(widget, forms.SelectMultiple):
                css = "field field-select"
            elif isinstance(widget, forms.Select):
                css = "field field-select"
            elif isinstance(widget, forms.Textarea):
                css = "field field-area"
            elif isinstance(widget, forms.ClearableFileInput):
                css = "field field-file"
            elif isinstance(widget, forms.DateInput):
                css = "field"
                widget.input_type = "date"
            elif isinstance(widget, forms.CheckboxInput):
                css = "field-check"
            else:
                css = "field"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = (existing + " " + css).strip()

        # Video fields: replaced by a browser→Cloudinary direct upload. The real
        # file input stays (so device pickers work), plus a hidden <name>_direct
        # field that receives the Cloudinary public_id without sending the bytes
        # through Vercel's 4.5 MB serverless function.
        for name in self._meta_video_fields():
            field = self.fields[name]
            field.required = False
            field.help_text = (field.help_text + " " if field.help_text else "") + (
                "Large videos upload directly to Cloudinary — full quality is kept."
            )
            widget = field.widget
            widget.attrs["accept"] = "video/*"
            widget.attrs["data-video-direct"] = "1"
            model_field = self._meta.model._meta.get_field(name)
            if isinstance(model_field.upload_to, str):
                media_prefix = getattr(settings, "MEDIA_URL", "media/").strip("/")
                folder = f"{media_prefix}/{model_field.upload_to.strip('/')}".strip("/")
                widget.attrs["data-folder"] = folder
            self.fields[f"{name}_direct"] = forms.CharField(
                required=False, widget=forms.HiddenInput()
            )
            self.fields[f"{name}_direct"].widget.attrs["class"] = "video-direct-id"

    def _meta_video_fields(self):
        meta = getattr(type(self), "Meta", None)
        names = getattr(meta, "video_fields", ()) if meta else ()
        return [name for name in names if name in self.fields]

    def save(self, commit=True):
        obj = super().save(commit=False)
        for name in self._meta_video_fields():
            direct = (self.cleaned_data.get(f"{name}_direct") or "").strip()
            if not direct or "://" in direct:
                continue
            # Store the Cloudinary public_id reference directly — no re-upload.
            setattr(obj, name, direct)
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    def _ensure_unique_slug(self, source_fields=("name", "title")):
        """Return a URL-safe unique slug, filling it from a text field when empty."""
        slug = (self.cleaned_data.get("slug") or "").strip()
        if slug:
            return slug
        base = ""
        for field_name in source_fields:
            base = self.cleaned_data.get(field_name)
            if base:
                break
        base = slugify(base or "")
        candidate = base or "item"
        queryset = self._meta.model._default_manager.all()
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        suffix = 2
        while queryset.filter(slug=candidate).exists():
            candidate = f"{base}-{suffix}" if base else f"item-{suffix}"
            suffix += 1
        return candidate


# ---------------------------------------------------------------------------
# Content forms
# ---------------------------------------------------------------------------


class ServiceForm(PortalModelForm):
    class Meta:
        model = Service
        fields = [
            "name", "slug", "icon_key", "tagline", "short_description",
            "description", "image", "video", "video_poster",
            "is_featured", "is_active", "sort_order",
        ]
        video_fields = ("video",)
        widgets = {
            "icon_key": forms.TextInput(
                attrs={"placeholder": "e.g. wedding, prewedding, maternity, baby"}
            ),
            "tagline": forms.TextInput(attrs={"placeholder": "Short line shown on cards"}),
            "description": forms.Textarea(
                attrs={"rows": 6, "placeholder": "Full description shown on the service page."}
            ),
        }

    def clean_slug(self):
        return self._ensure_unique_slug()


class PackageForm(PortalModelForm):
    features_text = forms.CharField(
        label="Features",
        required=False,
        help_text="One per line — label and value split by “|”. e.g. “2 Photographers | Full day”.",
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "2 Photographers | Full day coverage"}),
    )

    class Meta:
        model = Package
        fields = [
            "name", "category", "services", "price", "old_price",
            "description", "thumbnail", "photographers", "videographers",
            "hours", "edited_photos", "reels", "cinematic_film", "album",
            "drone", "full_day_coverage", "same_day_edit", "deliverables",
            "is_featured", "is_active", "sort_order",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "deliverables": forms.Textarea(
                attrs={"rows": 4, "placeholder": "One deliverable per line."}
            ),
            "services": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["services"].queryset = Service.objects.order_by("sort_order", "name")
        if self.instance.pk:
            self.fields["features_text"].initial = "\n".join(
                f"{feature.label} | {feature.value}"
                for feature in self.instance.features.all()
            )

    def save(self, commit=True):
        package = super().save(commit=commit)
        if commit:
            PackageFeature.objects.filter(package=package).delete()
            for line in self.cleaned_data.get("features_text", "").splitlines():
                line = line.strip()
                if not line:
                    continue
                label, separator, value = line.partition("|")
                PackageFeature.objects.create(
                    package=package,
                    label=(label or "").strip(),
                    value=(value or "").strip() if separator else "",
                )
        return package


class OfferForm(PortalModelForm):
    class Meta:
        model = Offer
        fields = [
            "title", "slug", "description", "services", "included_services",
            "original_price", "offer_price", "start_date", "end_date",
            "image", "video", "is_featured", "is_active", "sort_order",
        ]
        video_fields = ("video",)
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "included_services": forms.Textarea(
                attrs={"rows": 4, "placeholder": "One item per line — shown as a checklist."}
            ),
            "services": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["services"].queryset = Service.objects.order_by("sort_order", "name")

    def clean_slug(self):
        return self._ensure_unique_slug()


class TestimonialForm(PortalModelForm):
    class Meta:
        model = Testimonial
        fields = [
            "client_name", "client_photo", "event_type", "city", "rating",
            "review", "is_featured", "is_active", "sort_order",
        ]
        widgets = {
            "event_type": forms.TextInput(attrs={"placeholder": "e.g. Wedding"}),
            "review": forms.Textarea(
                attrs={"rows": 5, "placeholder": "What did the client say?"}
            ),
        }


class PortfolioImageForm(PortalModelForm):
    class Meta:
        model = PortfolioImage
        fields = [
            "category", "title", "image", "alt_text", "description",
            "is_featured", "is_active", "sort_order",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Short title for this photo"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = PortfolioCategory.objects.order_by("sort_order", "name")
        self.fields["category"].empty_label = "Uncategorised"


class PortfolioVideoForm(PortalModelForm):
    class Meta:
        model = PortfolioVideo
        fields = [
            "category", "title", "video", "youtube_url", "poster",
            "is_featured", "is_active", "sort_order",
        ]
        video_fields = ("video",)
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Short title for this film"}),
            "youtube_url": forms.URLInput(attrs={"placeholder": "https://www.youtube.com/watch?v=…"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = PortfolioCategory.objects.order_by("sort_order", "name")
        self.fields["category"].empty_label = "Uncategorised"


class PortfolioCategoryForm(PortalModelForm):
    class Meta:
        model = PortfolioCategory
        fields = ["name", "slug", "is_active", "sort_order"]

    def clean_slug(self):
        return self._ensure_unique_slug()


class CityForm(PortalModelForm):
    class Meta:
        model = City
        fields = ["name", "is_featured", "is_active", "sort_order"]


class HeroVideoForm(PortalModelForm):
    class Meta:
        model = HeroVideo
        fields = ["title", "video", "poster", "is_featured", "is_active", "sort_order"]
        video_fields = ("video",)


class TeamMemberForm(PortalModelForm):
    class Meta:
        model = TeamMember
        fields = ["name", "role", "photo", "is_developer", "bio", "is_active", "sort_order"]
        widgets = {
            "role": forms.TextInput(attrs={"placeholder": "e.g. Lead Photographer"}),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }


class SiteSettingsForm(PortalModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "brand_name", "logo", "tagline", "site_description",
            "phones", "whatsapp_number", "email", "address",
            "instagram", "facebook", "youtube",
            "home_hero_title", "home_hero_subtitle", "hero_fallback",
            "years_experience", "events_shot", "happy_clients",
        ]
        widgets = {
            "site_description": forms.Textarea(attrs={"rows": 3}),
            "address": forms.Textarea(attrs={"rows": 2}),
        }


# ---------------------------------------------------------------------------
# List helpers
# ---------------------------------------------------------------------------


def _badge(on):
    return format_html(
        '<span class="ap-badge {}">{}</span>',
        "is-on" if on else "is-off",
        "Yes" if on else "No",
    )


def _thumb(obj, attr="image"):
    image = getattr(obj, attr, None)
    if not image:
        return "\u2014"
    return format_html(
        '<img class="ap-thumb" src="{}" alt="{}" loading="lazy">',
        image.url,
        getattr(obj, "title", "") or "",
    )


def _file_badge(obj, attr="video"):
    return format_html(
        '<span class="ap-badge {}">{}</span>',
        "is-on" if getattr(obj, attr, None) else "is-off",
        "Yes" if getattr(obj, attr, None) else "No",
    )


# ---------------------------------------------------------------------------
# Section registry
# ---------------------------------------------------------------------------


class ContentSection:
    def __init__(
        self,
        key,
        model,
        form,
        name,
        singular,
        desc,
        list_display,
        search_fields=(),
        per_page=15,
        singleton=False,
    ):
        self.key = key
        self.model = model
        self.form = form
        self.name = name
        self.singular = singular
        self.desc = desc
        self.list_display = list_display
        self.search_fields = search_fields
        self.per_page = per_page
        self.singleton = singleton


CONTENT_SECTIONS = {
    "services": ContentSection(
        key="services",
        model=Service,
        form=ServiceForm,
        name="Services",
        singular="service",
        desc="Wedding, pre-wedding, baby & more",
        list_display=[
            {"label": "Photo", "value": lambda o: _thumb(o, "image"), "html": True},
            {"label": "Name", "value": "name"},
            {"label": "Tagline", "value": "tagline"},
            {"label": "Featured", "value": lambda o: _badge(o.is_featured), "html": True},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["name", "tagline", "short_description"],
    ),
    "packages": ContentSection(
        key="packages",
        model=Package,
        form=PackageForm,
        name="Packages",
        singular="package",
        desc="Pricing, coverage & features",
        list_display=[
            {"label": "Photo", "value": lambda o: _thumb(o, "thumbnail"), "html": True},
            {"label": "Name", "value": "name"},
            {"label": "Category", "value": lambda o: o.get_category_display()},
            {"label": "Price", "value": lambda o: f"\u20b9{o.price:,}"},
            {"label": "Featured", "value": lambda o: _badge(o.is_featured), "html": True},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["name", "description"],
    ),
    "offers": ContentSection(
        key="offers",
        model=Offer,
        form=OfferForm,
        name="Offers",
        singular="offer",
        desc="Season combos & discounts",
        list_display=[
            {"label": "Photo", "value": lambda o: _thumb(o, "image"), "html": True},
            {"label": "Title", "value": "title"},
            {"label": "Price", "value": lambda o: f"\u20b9{o.offer_price:,}"},
            {"label": "Original", "value": lambda o: f"\u20b9{o.original_price:,}"},
            {"label": "Featured", "value": lambda o: _badge(o.is_featured), "html": True},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["title", "description"],
    ),
    "testimonials": ContentSection(
        key="testimonials",
        model=Testimonial,
        form=TestimonialForm,
        name="Testimonials",
        singular="testimonial",
        desc="Client reviews & ratings",
        list_display=[
            {"label": "Photo", "value": lambda o: _thumb(o, "client_photo"), "html": True},
            {"label": "Client", "value": "client_name"},
            {"label": "Event", "value": "event_type"},
            {"label": "City", "value": "city"},
            {"label": "Rating", "value": lambda o: f"{o.rating}\u2605"},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["client_name", "city", "review"],
    ),
    "portfolio-photos": ContentSection(
        key="portfolio-photos",
        model=PortfolioImage,
        form=PortfolioImageForm,
        name="Portfolio Photos",
        singular="photo",
        desc="Gallery images per category",
        list_display=[
            {"label": "Photo", "value": lambda o: _thumb(o, "image"), "html": True},
            {"label": "Title", "value": "title"},
            {"label": "Category", "value": lambda o: o.category.name if o.category else "\u2014"},
            {"label": "Featured", "value": lambda o: _badge(o.is_featured), "html": True},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["title", "alt_text", "description"],
        per_page=20,
    ),
    "portfolio-videos": ContentSection(
        key="portfolio-videos",
        model=PortfolioVideo,
        form=PortfolioVideoForm,
        name="Portfolio Videos",
        singular="video",
        desc="Films & highlight reels",
        list_display=[
            {"label": "Poster", "value": lambda o: _thumb(o, "poster"), "html": True},
            {"label": "Title", "value": "title"},
            {"label": "Category", "value": lambda o: o.category.name if o.category else "\u2014"},
            {"label": "File", "value": lambda o: _file_badge(o, "video"), "html": True},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["title"],
        per_page=20,
    ),
    "portfolio-categories": ContentSection(
        key="portfolio-categories",
        model=PortfolioCategory,
        form=PortfolioCategoryForm,
        name="Portfolio Categories",
        singular="category",
        desc="Wedding, Pre-Wedding, Baby\u2026",
        list_display=[
            {"label": "Name", "value": "name"},
            {"label": "Slug", "value": "slug"},
            {"label": "Photos", "value": lambda o: o.images.count()},
            {"label": "Videos", "value": lambda o: o.videos.count()},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["name"],
    ),
    "cities": ContentSection(
        key="cities",
        model=City,
        form=CityForm,
        name="Cities",
        singular="city",
        desc="Cities you serve",
        list_display=[
            {"label": "Name", "value": "name"},
            {"label": "Featured", "value": lambda o: _badge(o.is_featured), "html": True},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
            {"label": "Sort", "value": "sort_order"},
        ],
        search_fields=["name"],
    ),
    "hero-videos": ContentSection(
        key="hero-videos",
        model=HeroVideo,
        form=HeroVideoForm,
        name="Hero Videos",
        singular="hero video",
        desc="Homepage background films",
        list_display=[
            {"label": "Title", "value": "title"},
            {"label": "File", "value": lambda o: _file_badge(o, "video"), "html": True},
            {"label": "Poster", "value": lambda o: _badge(bool(o.poster)), "html": True},
            {"label": "Featured", "value": lambda o: _badge(o.is_featured), "html": True},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["title"],
    ),
    "team": ContentSection(
        key="team",
        model=TeamMember,
        form=TeamMemberForm,
        name="Team",
        singular="team member",
        desc="Photographers & staff",
        list_display=[
            {"label": "Photo", "value": lambda o: _thumb(o, "photo"), "html": True},
            {"label": "Name", "value": "name"},
            {"label": "Role", "value": "role"},
            {"label": "Developer", "value": lambda o: _badge(o.is_developer), "html": True},
            {"label": "Active", "value": lambda o: _badge(o.is_active), "html": True},
        ],
        search_fields=["name", "role"],
    ),
    "site-settings": ContentSection(
        key="site-settings",
        model=SiteSettings,
        form=SiteSettingsForm,
        name="Site Settings",
        singular="site settings",
        desc="Brand, contacts & homepage text",
        list_display=[
            {"label": "Brand", "value": "brand_name"},
            {"label": "Phone", "value": "phones"},
            {"label": "Email", "value": "email"},
        ],
        singleton=True,
    ),
}
