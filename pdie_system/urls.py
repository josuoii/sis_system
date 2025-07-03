# Main project urls.py (pdie_system/urls.py)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    # Include intervention URLs first so /admin/link-requests/ etc. go to the app, not Django admin
    path('', include('intervention.urls')),
    path('django-admin/', admin.site.urls),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add this line to serve static files during development
urlpatterns += staticfiles_urlpatterns()