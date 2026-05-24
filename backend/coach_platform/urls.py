from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve


def health_check(request):
    return JsonResponse({"status": "ok", "service": "coach-platform-api"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.api_urls")),
    path("", health_check, name="health-check"),
]

if settings.DEBUG or settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
