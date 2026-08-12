import json
import re
import urllib.parse

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .content import CONTENT_SECTIONS
from .health import HEALTH_LABELS, build_health_report

HEX_COLOR_RE = re.compile(r"^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$")

THEME_COLOR_KEYS = [
    "background", "background_secondary", "ink", "ink_secondary",
    "ivory", "ivory_secondary", "cream", "primary",
    "primary_strong", "primary_deep", "muted", "muted_secondary",
]


def is_hex_color(value):
    return bool(HEX_COLOR_RE.match(value))


def _current_preset(theme):
    """Return the preset key matching the current theme colours, if any."""
    for preset in THEME_PRESETS:
        colors = preset["colors"]
        if all(getattr(theme, key, "") == colors.get(key) for key in ("primary", "primary_strong", "background", "background_secondary")):
            return preset["key"]
    return None


def theme_json(request):
    """Public JSON snapshot of the live theme — used for instant cross-tab updates."""
    theme = ThemeSettings.load()
    data = {"is_custom": theme.is_custom, "container_width": theme.container_width}
    for key in THEME_COLOR_KEYS:
        data[key] = getattr(theme, key)
    data["heading_font"] = theme.heading_font
    data["body_font"] = theme.body_font
    return JsonResponse(data)

from .forms import EnquiryForm
from .models import (
    BODY_FONTS,
    BUDGET_CHOICES,
    ENQUIRY_STATUS,
    HEADING_FONTS,
    City,
    Enquiry,
    HeroVideo,
    Offer,
    Package,
    PortfolioCategory,
    PortfolioImage,
    PortfolioVideo,
    Service,
    SiteSettings,
    TeamMember,
    Testimonial,
    ThemeSettings,
    THEME_PRESETS,
)

# slug -> (template name, human heading)
SERVICE_PAGES = {
    "wedding": ("services/wedding.html", "Wedding"),
    "pre-wedding": ("services/prewedding.html", "Pre-Wedding"),
    "engagement": ("services/engagement.html", "Engagement & Couple"),
    "baby": ("services/baby.html", "Baby"),
    "maternity": ("services/maternity.html", "Maternity"),
}


def _wa_link(message):
    site = SiteSettings.load()
    url = f"https://wa.me/{site.whatsapp_number}?text={urllib.parse.quote(message)}"
    return url


def _visible_offers():
    return [o for o in Offer.objects.filter(is_active=True) if o.is_current]


def _featured_offers():
    offers = Offer.objects.filter(is_active=True, is_featured=True)
    return [o for o in offers if o.is_current]


def _visible_packages():
    return list(Package.objects.filter(is_active=True))


def home(request):
    site = SiteSettings.load()
    hero_videos = list(HeroVideo.objects.filter(is_active=True).order_by("-is_featured", "sort_order"))

    context = {
        "active": "home",
        "hero_videos": hero_videos,
        "hero_fallback": site.hero_fallback,
        "hero_title": site.home_hero_title,
        "hero_subtitle": site.home_hero_subtitle,
        "featured_services": list(Service.objects.filter(is_active=True, is_featured=True)),
        "offers": _featured_offers()[:3],
        "testimonials": list(Testimonial.objects.filter(is_active=True, is_featured=True))[:5],
        "packages": [p for p in Package.objects.filter(is_active=True, is_featured=True)][:3],
        "stories": list(PortfolioImage.objects.filter(is_active=True, is_featured=True))[:8],
        "stats": {
            "years": site.years_experience,
            "events": site.events_shot,
            "clients": site.happy_clients,
            "cities": City.objects.filter(is_active=True).count() or 0,
        },
    }
    return render(request, "pages/home.html", context)


def about(request):
    site = SiteSettings.load()
    members = list(TeamMember.objects.filter(is_active=True))
    team_developer = next((m for m in members if m.is_developer), None)
    context = {
        "active": "about",
        "team_developer": team_developer,
        "team": [m for m in members if not m.is_developer],
        "services": list(Service.objects.filter(is_active=True)),
        "stats_facts": [
            {"value": site.years_experience, "label": "Years of craft"},
            {"value": site.events_shot, "label": "Events filmed"},
            {"value": site.happy_clients, "label": "Happy families"},
            {"value": City.objects.filter(is_active=True).count() or 0, "label": "Cities & beyond"},
        ],
    }
    return render(request, "pages/about.html", context)


def services(request):
    context = {
        "active": "services",
        "services": list(Service.objects.filter(is_active=True)),
    }
    return render(request, "pages/services.html", context)


def _service_page(request, slug):
    if slug not in SERVICE_PAGES:
        raise Http404
    template_name, heading = SERVICE_PAGES[slug]

    service = Service.objects.filter(slug=slug, is_active=True).first()
    portfolio_category = None
    if service:
        portfolio_category = PortfolioCategory.objects.filter(slug=slug, is_active=True).first()

    # Offers linked to this service (falls back to all current offers)
    linked = Offer.objects.filter(is_active=True, services=service) if service else Offer.objects.none()
    offers = [o for o in linked if o.is_current] or _featured_offers()

    # Packages linked to this service (falls back to featured packages).
    if service:
        linked_packages = Package.objects.filter(is_active=True, services=service)
    else:
        linked_packages = Package.objects.none()
    packages = list(linked_packages) or [p for p in Package.objects.filter(is_active=True, is_featured=True)]

    # Gallery images and videos for this category, with a couple of generic fallbacks.
    images = list(
        PortfolioImage.objects.filter(is_active=True, category=portfolio_category)
        if portfolio_category
        else PortfolioImage.objects.none()
    )
    videos = list(
        PortfolioVideo.objects.filter(is_active=True, category=portfolio_category)
        if portfolio_category
        else PortfolioVideo.objects.none()
    )
    if not images:
        images = list(PortfolioImage.objects.filter(is_active=True, is_featured=True))[:6]
    if not videos:
        videos = list(PortfolioVideo.objects.filter(is_active=True, is_featured=True))[:3]

    testimonials = list(
        Testimonial.objects.filter(is_active=True, is_featured=True)
    )[:6]

    context = {
        "active": "services",
        "parent_url": "/services/",
        "service": service,
        "page_heading": heading,
        "page_slug": slug,
        "offers": offers[:4],
        "packages": packages[:4],
        "images": images,
        "videos": videos,
        "testimonials": testimonials,
        "hero_wa": _wa_link(f"Hi! I'm interested in your {heading} photography and videography."),
    }
    return render(request, template_name, context)


def service_detail(request, slug):
    return _portfolio_slug_dispatch(request, slug)


def _portfolio_slug_dispatch(request, slug):
    """Dispatch /services/<slug>/ to the correct template, 404 if unknown."""
    return _service_page(request, slug)


def wedding(request):
    return _service_page(request, "wedding")


def prewedding(request):
    return _service_page(request, "pre-wedding")


def engagement(request):
    return _service_page(request, "engagement")


def baby(request):
    return _service_page(request, "baby")


def maternity(request):
    return _service_page(request, "maternity")


def portfolio(request):
    selected = request.GET.get("category", "all")
    categories = list(PortfolioCategory.objects.filter(is_active=True).order_by("sort_order"))
    images = list(PortfolioImage.objects.filter(is_active=True))
    videos = list(PortfolioVideo.objects.filter(is_active=True))
    selected_category = None

    if selected != "all":
        selected_category = next((c for c in categories if c.slug == selected), None)
        if selected_category is None:
            raise Http404("Category not found")
        images = [i for i in images if i.category_id == selected_category.id]
        videos = [v for v in videos if v.category_id == selected_category.id]

    context = {
        "active": "portfolio",
        "categories": categories,
        "selected": selected,
        "selected_category": selected_category,
        "images": images,
        "videos": videos,
        "count": len(images) + len(videos),
    }
    return render(request, "pages/portfolio.html", context)


def packages(request):
    groups = {}
    for label in ["affordable", "classic", "premium", "luxury"]:
        group_pkgs = [p for p in _visible_packages() if p.category == label]
        if group_pkgs:
            groups.setdefault(
                label,
                {
                    "label": dict(Package._meta.get_field("category").choices).get(label),
                    "packages": group_pkgs,
                },
            )

    context = {
        "active": "packages",
        "groups": [
            {"key": k, "label": v["label"], "packages": v["packages"]}
            for k, v in groups.items()
        ],
    }
    return render(request, "pages/packages.html", context)


def offers(request):
    featured = _featured_offers()
    featured_ids = {o.pk for o in featured}
    others = [o for o in _visible_offers() if o.pk not in featured_ids]
    context = {
        "active": "offers",
        "offers": featured + others,
    }
    return render(request, "pages/offers.html", context)


def testimonials(request):
    testimonials_active = list(Testimonial.objects.filter(is_active=True))
    context = {
        "active": "testimonials",
        "testimonials": testimonials_active,
    }
    return render(request, "pages/testimonials.html", context)


def contact(request):
    initial = {}
    package = request.GET.get("package")
    offer = request.GET.get("offer")
    if package:
        initial["message"] = f"I'm interested in the '{package}' package."
    elif offer:
        initial["message"] = f"I'm interested in the '{offer}' offer."

    if request.method == "POST":
        form = EnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save()
            enquiry.notes = f"Received via website ({request.build_absolute_uri()})"
            enquiry.save(update_fields=["notes"])
            messages.success(
                request,
                f"Thank you, {enquiry.name}! Your enquiry has been received. We\u2019ll reach out shortly.",
            )
            success_link = _wa_link(
                f"Hi! I'd like to follow up on my enquiry for {enquiry.service or 'your services'}. "
                f"My number is {enquiry.phone}."
            )
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": True, "wa_link": success_link})
            return redirect("/contact/?submitted=1")
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors})

    form = EnquiryForm(initial=initial)
    context = {
        "active": "contact",
        "submitted": request.GET.get("submitted") == "1",
        "form": form,
        "budget_choices": BUDGET_CHOICES,
        "services_choices": list(Service.objects.filter(is_active=True)),
    }
    return render(request, "pages/contact.html", context)


# ---------------------------------------------------------------------------
# Admin portal (branded login + dashboard over the Django admin CMS)
# ---------------------------------------------------------------------------

PORTAL_LINKS = [
    {
        "key": "services",
        "name": "Services",
        "desc": "Wedding, pre-wedding, baby & more",
    },
    {
        "key": "packages",
        "name": "Packages",
        "desc": "Pricing, coverage & features",
    },
    {
        "key": "offers",
        "name": "Offers",
        "desc": "Season combos & discounts",
    },
    {
        "key": "testimonials",
        "name": "Testimonials",
        "desc": "Client reviews & ratings",
    },
    {
        "key": "portfolio-photos",
        "name": "Portfolio Photos",
        "desc": "Gallery images per category",
    },
    {
        "key": "portfolio-videos",
        "name": "Portfolio Videos",
        "desc": "Films & highlight reels",
    },
    {
        "key": "portfolio-categories",
        "name": "Portfolio Categories",
        "desc": "Wedding, Pre-Wedding, Baby\u2026",
    },
    {
        "key": "cities",
        "name": "Cities",
        "desc": "Cities you serve",
    },
    {
        "key": "hero-videos",
        "name": "Hero Videos",
        "desc": "Homepage background films",
    },
    {
        "key": "team",
        "name": "Team",
        "desc": "Photographers & staff",
    },
    {
        "key": "site-settings",
        "name": "Site Settings",
        "desc": "Brand, contacts & homepage text",
    },
]

STATUS_COLOR = {
    "NEW": "gold",
    "CONTACTED": "blue",
    "FOLLOW_UP": "orange",
    "BOOKED": "green",
    "COMPLETED": "teal",
    "CLOSED": "grey",
}


def _portal_context(request):
    enquiries = Enquiry.objects.all()
    context = {
        "portal_user": request.user,
        "portal_links": PORTAL_LINKS,
        "status_choices": ENQUIRY_STATUS,
        "status_color": STATUS_COLOR,
        "stats": {
            "enquiries_total": enquiries.count(),
            "enquiries_new": enquiries.filter(status="NEW").count(),
            "services": Service.objects.count(),
            "packages": Package.objects.count(),
            "photos": PortfolioImage.objects.count(),
            "videos": PortfolioVideo.objects.count(),
            "offers": Offer.objects.count(),
            "testimonials": Testimonial.objects.count(),
            "cities": City.objects.filter(is_active=True).count(),
        },
        "recent_enquiries": list(enquiries.select_related("service")[:8]),
        "budget_map": dict(BUDGET_CHOICES),
        "theme": ThemeSettings.load(),
        "heading_fonts": HEADING_FONTS,
        "body_fonts": BODY_FONTS,
        "theme_presets": [
            {
                "key": p["key"],
                "name": p["name"],
                "description": p["description"],
                "heading": p["heading"],
                "body": p["body"],
                "swatches": [
                    p["colors"]["primary"],
                    p["colors"]["primary_strong"],
                    p["colors"]["background"],
                    p["colors"]["ivory"],
                ],
                "colors_json": json.dumps(p["colors"]),
            }
            for p in THEME_PRESETS
        ],
        "current_preset": _current_preset(ThemeSettings.load()),
        "theme_color_fields": [
            {"key": "background", "label": "Page background"},
            {"key": "background_secondary", "label": "Card / section background"},
            {"key": "ink", "label": "Dark text (on light)"},
            {"key": "ink_secondary", "label": "Dark text secondary"},
            {"key": "ivory", "label": "Light text / surface"},
            {"key": "ivory_secondary", "label": "Light surface secondary"},
            {"key": "cream", "label": "Light page background"},
            {"key": "primary", "label": "Brand accent"},
            {"key": "primary_strong", "label": "Bright accent (hover)"},
            {"key": "primary_deep", "label": "Deep accent"},
            {"key": "muted", "label": "Muted text"},
            {"key": "muted_secondary", "label": "Fainter text"},
        ],
    }
    health_report = build_health_report()
    context["health"] = health_report
    context["health_json"] = json.dumps(health_report)
    context["health_labels"] = HEALTH_LABELS
    return context


def admin_portal(request):
    if request.method == "POST":
        action = request.POST.get("portal_action")

        if action == "login":
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "")
            user = authenticate(request, username=username, password=password)
            if user is not None and (user.is_staff or user.is_superuser):
                login(request, user)
                return redirect("main:admin_portal")
            return render(
                request,
                "admin_portal.html",
                {"login_error": True, "login_username": username},
            )

        if action == "status" and request.user.is_authenticated:
            enquiry_id = request.POST.get("enquiry_id", "")
            new_status = request.POST.get("status", "")
            valid_statuses = {value for value, _label in ENQUIRY_STATUS}
            if enquiry_id.isdigit() and new_status in valid_statuses:
                Enquiry.objects.filter(pk=enquiry_id).update(status=new_status)
                messages.success(request, "Enquiry status updated.")
            return redirect("main:admin_portal")

        if action == "theme" and request.user.is_authenticated:
            theme = ThemeSettings.load()

            if request.POST.get("reset_theme"):
                for field in theme._meta.get_fields():
                    if hasattr(field, "default") and field.name in (
                        "background", "background_secondary", "ink", "ink_secondary",
                        "ivory", "ivory_secondary", "cream", "primary",
                        "primary_strong", "primary_deep", "muted", "muted_secondary",
                        "heading_font", "body_font", "container_width",
                    ):
                        setattr(theme, field.name, field.default if not callable(field.default) else field.default())
                theme.is_custom = True
                theme.save()
                messages.success(request, "Theme reset to the default design.")
                return redirect("main:admin_portal")

            valid_fonts = {value for value, _label in HEADING_FONTS + BODY_FONTS}

            bad = []
            for key in THEME_COLOR_KEYS:
                value = request.POST.get(key, "").strip().lower()
                if not is_hex_color(value):
                    bad.append(key)
            width_raw = request.POST.get("container_width", "").strip()
            width_ok = width_raw.isdigit() and 900 <= int(width_raw) <= 2000
            heading = request.POST.get("heading_font", "")
            body = request.POST.get("body_font", "")

            if bad or not width_ok or heading not in valid_fonts or body not in valid_fonts:
                messages.error(request, "Theme not saved — invalid colour, width or font value.")
                return redirect("main:admin_portal")

            theme.is_custom = request.POST.get("is_custom") == "on"
            for key in THEME_COLOR_KEYS:
                setattr(theme, key, request.POST.get(key).strip().lower())
            theme.container_width = int(width_raw)
            theme.heading_font = heading
            theme.body_font = body
            theme.save()
            messages.success(request, "Theme settings saved — refresh the site to see the new look.")
            return redirect("main:admin_portal")

    can_manage = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    if can_manage:
        return render(request, "admin_portal.html", _portal_context(request))
    return render(request, "admin_portal.html", {})


def admin_portal_logout(request):
    logout(request)
    return redirect("main:admin_portal")


def portal_health(request):
    """JSON snapshot of live server, database and media-storage usage (staff only)."""
    can_manage = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    if not can_manage:
        return JsonResponse({"error": "unauthorized"}, status=403)
    return JsonResponse(build_health_report())


# ---------------------------------------------------------------------------
# Frontend content manager (replaces the embedded Django admin iframe)
# ---------------------------------------------------------------------------


def _portal_section(request, key):
    """Resolve a content section key, guarding the portal behind staff login."""
    section = CONTENT_SECTIONS.get(key)
    can_manage = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    if section is None or not can_manage:
        raise Http404("Unknown content section")
    return section


def portal_upload_debug(request):
    """Show what the CURRENT deployed server reads for the upload config."""
    can_manage = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    if not can_manage:
        raise Http404("Not found")

    from django.conf import settings

    cloud = settings.CLOUDINARY_STORAGE.get("CLOUD_NAME", "")
    preset = getattr(settings, "CLOUDINARY_UPLOAD_PRESET", "")
    return JsonResponse(
        {
            "cloud_name": cloud,
            "cloud_name_set": bool(cloud),
            "upload_preset": preset,
            "upload_preset_set": bool(preset),
            "remote_debug": True,
            "hint": (
                "If upload_preset_set is false here, the env var is missing from THIS deployment. "
                "In Vercel add the variable individually (name must be exactly CLOUDINARY_UPLOAD_PRESET), "
                "select Environment: Production, save, then Redeploy."
            ),
        }
    )


def portal_content_list(request, key):
    section = _portal_section(request, key)

    # Singletons (e.g. site settings) are edited directly rather than listed.
    if section.singleton:
        obj = section.model.objects.first()
        if obj is not None:
            return redirect("main:portal_content_edit", key=key, pk=obj.pk)
        return redirect("main:portal_content_add", key=key)

    queryset = section.model.objects.all()

    query = (request.GET.get("q") or "").strip()
    if query and section.search_fields:
        lookup = Q()
        for field in section.search_fields:
            lookup |= Q(**{f"{field}__icontains": query})
        queryset = queryset.filter(lookup)

    page_obj = Paginator(queryset, section.per_page).get_page(request.GET.get("page"))

    rows = []
    for obj in page_obj.object_list:
        cells = []
        for column in section.list_display:
            source = column["value"]
            value = source(obj) if callable(source) else getattr(obj, source, "")
            cells.append({"value": value, "html": bool(column.get("html"))})
        rows.append({"pk": obj.pk, "cells": cells})

    context = {
        "section": section,
        "rows": rows,
        "page_obj": page_obj,
        "query": query,
    }
    return render(request, "admin_portal/content_list.html", context)


def _portal_cloudinary_config():
    from django.conf import settings

    return {
        "cloudName": settings.CLOUDINARY_STORAGE.get("CLOUD_NAME", ""),
        "uploadPreset": getattr(settings, "CLOUDINARY_UPLOAD_PRESET", ""),
    }


def portal_content_add(request, key):
    section = _portal_section(request, key)

    if section.singleton and section.model.objects.exists():
        obj = section.model.objects.first()
        return redirect("main:portal_content_edit", key=key, pk=obj.pk)

    if request.method == "POST":
        form = section.form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"{section.singular.capitalize()} added successfully.")
            return redirect("main:portal_content_list", key=key)
    else:
        form = section.form()

    context = {
        "section": section,
        "form": form,
        "title": f"Add {section.singular}",
        "object": None,
        "cloudinary_config": _portal_cloudinary_config(),
    }
    return render(request, "admin_portal/content_form.html", context)


def portal_content_edit(request, key, pk):
    section = _portal_section(request, key)
    obj = get_object_or_404(section.model, pk=pk)

    if request.method == "POST":
        form = section.form(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"{section.singular.capitalize()} updated.")
            return redirect("main:portal_content_list", key=key)
    else:
        form = section.form(instance=obj)

    context = {
        "section": section,
        "form": form,
        "title": f"Edit {section.singular}",
        "object": obj,
        "cloudinary_config": _portal_cloudinary_config(),
    }
    return render(request, "admin_portal/content_form.html", context)


def portal_content_delete(request, key, pk):
    section = _portal_section(request, key)
    if section.singleton:
        raise Http404("This section cannot be deleted")

    obj = get_object_or_404(section.model, pk=pk)
    if request.method == "POST":
        label = str(obj)
        obj.delete()
        messages.success(request, f"\u201c{label}\u201d was deleted.")
        return redirect("main:portal_content_list", key=key)

    context = {
        "section": section,
        "object": obj,
    }
    return render(request, "admin_portal/content_confirm_delete.html", context)