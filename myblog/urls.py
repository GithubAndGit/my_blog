"""myblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
import os, sys
BASE_PATH = os.path.dirname(os.getcwd())
sys.path.append(BASE_PATH)
from blog.views import IndexView, DetailView, ArchiveView, ArticleApiView, LoginView, RegisterView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", LoginView.login),
    path("register/", RegisterView.register),
    path("myblog/", IndexView.as_view()),
    path("archives/", ArchiveView.as_view()),
    path("api/article/", ArticleApiView.as_view()),
    path("<str:year>/<str:month>/<str:day>/<str:uri>", DetailView.as_view()),
    path("mdeditor/", include("mdeditor.urls")),
] + static(settings.STATIC_URL) + static(settings.MEDIA_ROOT, document_root=settings.MEDIA_ROOT)
