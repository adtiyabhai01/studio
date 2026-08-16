from django.contrib import admin
from django.utils.html import format_html

from .models import (
    City,
    Enquiry,
    ErrorLog,
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
    ThemeSettings,
)


@admin.register(ThemeSettings)
class ThemeSettingsAdmin(admin.ModelAdmin):
    list_display = ("swatch", "is_custom")
    fieldsets = (
        (
            "Brand colours",
            {"fields": ("primary", "primary_strong", "primary_deep")},
        ),
        (
            "Backgrounds",
            {"fields": ("background", "background_secondary", "cream")},
        ),
        (
            "Text & surfaces",
            {"fields": ("ivory", "ivory_secondary", "ink", "ink_secondary", "muted", "muted_secondary")},
        ),
        (
            "Typography & layout",
            {"fields": ("heading_font", "body_font", "container_width")},
        ),
        ("Visibility", {"fields": ("is_custom",)}),
    )

    @admin.display(description="Preview")
    def swatch(self, obj):
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:6px;">'
            '<span style="width:18px;height:18px;border-radius:50%;background:{};'
            'border:1px solid rgba(255,255,255,.35);display:inline-block"></span>'
            "{} {}</span>",
            obj.primary,
            obj.primary,
            obj.background,
        )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("brand_name", "tagline", "phone_display", "whatsapp_number")
    fieldsets = (
        ("Brand", {"fields": ("brand_name", "logo", "tagline", "site_description")}),
        (
            "Contact",
            {"fields": ("phones", "whatsapp_number", "email", "address")},
        ),
        ("Social", {"fields": ("instagram", "facebook", "youtube")}),
        (
            "Homepage Hero",
            {"fields": ("home_hero_title", "home_hero_subtitle", "hero_fallback")},
        ),
        ("Studio Stats", {"fields": ("years_experience", "events_shot", "happy_clients")}),
    )

    def phone_display(self, obj):
        return obj.phones

    phone_display.short_description = "Phone numbers"

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 1
    fields = ("image", "title", "alt_text", "is_featured", "is_active", "sort_order")


class PortfolioVideoInline(admin.TabularInline):
    model = PortfolioVideo
    extra = 0
    fields = ("video", "youtube_url", "poster", "title", "is_active", "sort_order")


@admin.register(PortfolioCategory)
class PortfolioCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "image_count", "video_count", "is_active", "sort_order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active", "sort_order")
    inlines = [PortfolioImageInline, PortfolioVideoInline]

    def image_count(self, obj):
        return obj.images.count()

    def video_count(self, obj):
        return obj.videos.count()


@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    list_display = ("preview", "title", "category", "is_featured", "is_active", "sort_date")
    list_filter = ("category", "is_featured", "is_active")
    search_fields = ("title", "alt_text", "description")
    list_editable = ("is_featured", "is_active")
    fieldsets = (
        (None, {"fields": (("category", "title"), "image", "alt_text", "description")}),
        ("Options", {"fields": ("is_featured", "is_active", "sort_order")}),
    )

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="64" height="44" style="object-fit:cover;border-radius:4px;">',
                obj.image.url,
            )
        return "—"

    def sort_date(self, obj):
        return obj.created_at

    sort_date.admin_order_field = "created_at"
    sort_date.short_description = "Added"


@admin.register(PortfolioVideo)
class PortfolioVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "has_file", "youtube_url", "is_featured", "is_active")
    list_filter = ("category", "is_featured", "is_active")
    search_fields = ("title",)
    list_editable = ("is_featured", "is_active")

    @admin.display(boolean=True, description="File")
    def has_file(self, obj):
        return bool(obj.video)


class ServiceInline(admin.TabularInline):
    model = Offer.services.through
    extra = 0
    verbose_name_plural = "Show this offer on services"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "icon_key", "slug", "is_featured", "is_active", "sort_order")
    list_editable = ("is_featured", "is_active", "sort_order")
    search_fields = ("name", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "icon_key", "slug", "tagline", "short_description")}),
        ("Details", {"fields": ("description", "image", "video", "video_poster")}),
        ("Options", {"fields": ("is_featured", "is_active", "sort_order")}),
    )


class PackageFeatureInline(admin.TabularInline):
    model = PackageFeature
    extra = 1
    fields = ("label", "value")


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "old_price", "is_featured", "is_active")
    list_filter = ("category", "is_featured", "is_active")
    search_fields = ("name", "description")
    list_editable = ("is_featured", "is_active")
    fieldsets = (
        (None, {"fields": ("name", "category", "services", "thumbnail")}),
        ("Pricing", {"fields": ("price", "old_price")}),
        (
            "Coverage",
            {
                "fields": (
                    "photographers",
                    "videographers",
                    "hours",
                    "edited_photos",
                    "reels",
                    "full_day_coverage",
                )
            },
        ),
        (
            "Deliverables",
            {
                "fields": (
                    "cinematic_film",
                    "album",
                    "drone",
                    "same_day_edit",
                    "deliverables",
                )
            },
        ),
        ("Description & Sorting", {"fields": ("description", "sort_order", "is_featured", "is_active")}),
    )
    inlines = [PackageFeatureInline]


@admin.register(PackageFeature)
class PackageFeatureAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "package")
    search_fields = ("label", "value")
    autocomplete_fields = ("package",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("title", "offer_price", "original_price", "is_current", "is_featured", "is_active")
    list_filter = ("is_featured", "is_active", "start_date", "end_date")
    search_fields = ("title", "description")
    list_editable = ("is_featured", "is_active")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("services",)
    fieldsets = (
        (None, {"fields": ("title", "slug", "description")}),
        ("Pricing", {"fields": ("original_price", "offer_price")}),
        ("Dates", {"fields": ("start_date", "end_date")}),
        ("Assets", {"fields": ("image", "video")}),
        ("Included services (one per line)", {"fields": ("included_services",)}),
        ("Visibility", {"fields": ("services", "is_featured", "is_active", "sort_order")}),
    )

    def is_current(self, obj):
        return obj.is_current

    is_current.boolean = True


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("client_name", "event_type", "city", "rating", "is_featured", "is_active")
    list_filter = ("event_type", "city", "rating", "is_featured", "is_active")
    search_fields = ("client_name", "city", "review")
    list_editable = ("is_featured", "is_active")


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "developer", "is_active", "sort_order")
    list_filter = ("is_developer", "is_active")
    search_fields = ("name", "role")
    list_editable = ("is_active", "sort_order")
    fieldsets = (
        (None, {"fields": ("name", "role", "bio")}),
        ("Profile photo", {"fields": ("photo",)}),
        ("Position", {"fields": ("is_developer", "is_active", "sort_order")}),
    )

    @admin.display(boolean=True, description="Developer")
    def developer(self, obj):
        return obj.is_developer


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "service", "event_date", "city", "budget", "status", "created_at")
    list_filter = ("status", "budget", "service", "city", "created_at")
    search_fields = ("name", "phone", "email", "city", "message")
    list_editable = ("status",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    fieldsets = (
        (None, {"fields": ("name", "phone", "email")}),
        (
            "Event details",
            {"fields": ("service", "event_date", "city", "budget", "message")},
        ),
        ("Status", {"fields": ("status", "notes", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        obj.status = obj.status or "NEW"
        super().save_model(request, obj, form, change)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "is_featured", "is_active", "sort_order")
    list_editable = ("is_featured", "is_active", "sort_order")
    search_fields = ("name",)


@admin.register(HeroVideo)
class HeroVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "orientation", "is_featured", "is_active", "sort_order")
    list_editable = ("orientation", "is_featured", "is_active", "sort_order")
    fieldsets = (
        (None, {"fields": ("title", "video", "poster", "orientation")}),
        ("Options", {"fields": ("is_featured", "is_active", "sort_order")}),
    )


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """Error logs are written automatically — admin can review and delete only."""

    list_display = ("level", "message_preview", "path", "method", "status_code", "ip", "created_at")
    list_filter = ("level", "status_code", "created_at")
    search_fields = ("message", "path", "ip", "user", "traceback")
    readonly_fields = (
        "level", "message", "traceback", "path", "method",
        "status_code", "ip", "user", "user_agent", "created_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Message")
    def message_preview(self, obj):
        return obj.message[:90]