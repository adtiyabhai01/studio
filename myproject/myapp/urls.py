from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("services/wedding/", views.wedding, name="wedding"),
    path("services/pre-wedding/", views.prewedding, name="prewedding"),
    path("services/engagement/", views.engagement, name="engagement"),
    path("services/baby/", views.baby, name="baby"),
    path("services/maternity/", views.maternity, name="maternity"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path("portfolio/", views.portfolio, name="portfolio"),
    path("packages/", views.packages, name="packages"),
    path("offers/", views.offers, name="offers"),
    path("testimonials/", views.testimonials, name="testimonials"),
    path("contact/", views.contact, name="contact"),

    path("theme.json", views.theme_json, name="theme_json"),

    path("admin-portal/", views.admin_portal, name="admin_portal"),
    path("admin-portal/logout/", views.admin_portal_logout, name="admin_portal_logout"),
    path("admin-portal/health/", views.portal_health, name="portal_health"),

    # Frontend content manager
    path("admin-portal/content/<slug:key>/", views.portal_content_list, name="portal_content_list"),
    path("admin-portal/content/<slug:key>/add/", views.portal_content_add, name="portal_content_add"),
    path("admin-portal/content/<slug:key>/<int:pk>/", views.portal_content_edit, name="portal_content_edit"),
    path(
        "admin-portal/content/<slug:key>/<int:pk>/delete/",
        views.portal_content_delete,
        name="portal_content_delete",
    ),
]