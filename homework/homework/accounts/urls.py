from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from .views import MenuView, PartListView, DeletePartView, build_aircraft_view, produced_aircrafts_api, all_parts_api, build_aircraft
from . import views as html_views
from django.urls import path
from . import views

urlpatterns = [
    # API endpoint'leri
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('menu/', MenuView.as_view(), name='menu'),
    path('api/part-list/', PartListView.as_view(), name='part-list-api'),
    path('api/parts/', PartListView.as_view(), name='part-list-api'),
    path('api/parts/delete/', DeletePartView.as_view(), name='part-delete-api'),


    # HTML sayfa view'ları
    path('login-page/', views.login_page, name='html_login'),
    path('menu-page/', views.menu_page, name='menu-page'),  # Buraya dikkat!
    path('logout-page/', views.logout_page, name='html_logout'),
    path('register-page/', views.register_page, name='html_register'),
    path('parca-uret/', views.create_part, name='create_part'),
    path('build-aircraft/', build_aircraft_view, name='build_aircraft'),
    path('build-aircraft/', views.build_aircraft_view, name='build-aircraft'),
    path('build-aircraft/', views.build_aircraft_view, name='build-aircraft'),
    path('produced-aircrafts-api/', views.produced_aircrafts_api, name='produced-aircrafts-api'),
    path('api/all-parts/', views.all_parts_api, name='all-parts-api'),
]