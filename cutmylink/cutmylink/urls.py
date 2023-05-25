"""
URL configuration for cutmylink project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from link.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/link/', LinkAPIView.as_view()),
    path('api/v1/link/<int:pk>/delete', LinkAPIDelete.as_view()),
    path('api/v1/link/<int:pk>/update', LinkAPIUpdate.as_view()),
    path('api/v1/user/create', UserCreateAPIView.as_view()),
    path('<str:short_code>/', ShortLinkRedirectView.as_view(), name='shortlink-redirect'),
    path('api/v1/stat/', LinkStatView.as_view()),
]
