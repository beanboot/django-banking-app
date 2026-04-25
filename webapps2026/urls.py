from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard')),
    path('', include('register.urls')),
    path('', include('payapp.urls')),
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]
