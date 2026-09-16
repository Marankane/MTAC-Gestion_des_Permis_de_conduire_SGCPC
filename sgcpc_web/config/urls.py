from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="dossiers:liste")),
    path("comptes/", include("comptes.urls")),
    path("dossiers/", include("dossiers.urls")),
    path("commissions/", include("commissions.urls")),
    path("decisions/", include("decisions.urls")),
    path("restitution/", include("restitution.urls")),
    path("stats/", include("reporting_stats.urls")),
    path("api/v1/", include("config.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
