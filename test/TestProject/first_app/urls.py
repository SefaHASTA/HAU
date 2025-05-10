
from django.urls import path, include
from .views import country_list, country_detail, CountryView, CountryDetailView, GenericApiView,login, logout

urlpatterns = [
    path('list/', CountryView.as_view()),
    path('detail/<int:pk>', CountryDetailView.as_view()),
    path("generic/<int:id>", GenericApiView.as_view()),
    path('login/', login),
    path('logout/', logout),
]