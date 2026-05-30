from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from movie import views as mathew
from mokshang import views as mas

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', mathew.index),
    path('', mas.portfolio, name='portfolio'),
    path('portfolio/<str:username>/', mas.portfolio, name='portfolio_public'),
    path('register/', mas.register, name='register'),
    path('activate/<str:uidb64>/<str:token>/', mas.activate, name='activate'),
    path('login/', mas.login_view, name='login'),
    path('logout/', mas.logout_view, name='logout'),
    path('dashboard/', mas.dashboard, name='dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
