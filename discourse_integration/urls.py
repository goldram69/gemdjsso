# discourse_integration/urls.py

from django.urls import path
from . import views

app_name = 'discourse_integration' # Add app namespace

urlpatterns = [
    path('sso/login/', views.discourse_sso_login, name='discourse_sso_login'),
    path('sso/callback/', views.discourse_sso_callback, name='discourse_sso_callback'),
    # Add a view for the forum link
    path('forum/', views.discourse_forum_link, name='discourse_forum_link'),
]
```python
# your_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('discourse/', include('discourse_integration.urls', namespace='discourse')), # Include with namespace
    # Other project urls
]

# Serve static and media files in development (optional for basic setup)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # If you have media files


