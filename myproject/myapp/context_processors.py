from .models import City, Service, SiteSettings, ThemeSettings


CORE_PAGES = [
    ("home", "/", "Home"),
    ("about", "/about/", "About"),
    ("services", "/services/", "Services"),
    ("portfolio", "/portfolio/", "Portfolio"),
    ("packages", "/packages/", "Packages"),
    ("offers", "/offers/", "Offers"),
    ("testimonials", "/testimonials/", "Stories"),
    ("contact", "/contact/", "Contact"),
]


def site_context(request):
    site = SiteSettings.load()
    services = list(Service.objects.filter(is_active=True).order_by("sort_order", "name"))
    cities = list(City.objects.filter(is_active=True).order_by("sort_order", "name"))
    featured_cities = [c for c in cities if c.is_featured] or cities[:10]

    return {
        "site": site,
        "theme": ThemeSettings.load(),
        "services_list": services,
        "cities": cities,
        "featured_cities": featured_cities[:10],
        "nav_pages": CORE_PAGES,
        "wa_number": site.whatsapp_number,
        "wa_message": site.whatsapp_link(),
    }