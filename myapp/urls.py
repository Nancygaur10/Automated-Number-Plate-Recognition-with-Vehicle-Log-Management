from myapp import views
from django.urls import path

urlpatterns = [
    path("",views.home, name="home"),
    path("signup/", views.signup_view, name='signup'),
    path("admin/", views.admin_dashboard, name='admin_dashboard'),  #nancy
]

