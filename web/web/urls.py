from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls import url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('classification/', include('classification.urls')),
    url(r'^system-health/?', include('health_check.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
