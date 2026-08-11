from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return [
            "main:home",
            "main:about",
            "main:services",
            "main:wedding",
            "main:prewedding",
            "main:engagement",
            "main:baby",
            "main:maternity",
            "main:portfolio",
            "main:packages",
            "main:offers",
            "main:testimonials",
            "main:contact",
        ]

    def location(self, item):
        return reverse(item)