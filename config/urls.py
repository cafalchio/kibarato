"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from django.conf import settings
from django.conf.urls.static import static
from promotions.views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path(
        'robots.txt',
        TemplateView.as_view(template_name='robots.txt', content_type='text/plain'),
        name='robots',
    ),
    path(
        'sitemap.xml',
        TemplateView.as_view(template_name='sitemap.xml', content_type='application/xml'),
        name='sitemap',
    ),
    path('admin/promotions/', admin.site.admin_view(RedirectView.as_view(
        pattern_name='admin:promotions_promotion_changelist', permanent=False,
    ))),
    path('admin/', admin.site.admin_view(RedirectView.as_view(
        pattern_name='admin:promotions_promotion_changelist', permanent=False,
    ))),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
