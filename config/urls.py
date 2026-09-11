from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


def home(request):
    return JsonResponse({
        "message": "Confession Room API is running.",
        "status": "online",
    })


urlpatterns = [
    path("", home, name="home"),

    path("admin/", admin.site.urls),

    path("api/auth/", include("accounts.urls")),
    path("api/confessions/", include("confessions.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )