from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("kirish/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("chiqish/", auth_views.LogoutView.as_view(), name="logout"),
    path("royxatdan-otish/", views.register, name="register"),
    path("kabinet/", views.dashboard, name="dashboard"),
    path("kurs/<slug:slug>/", views.course_detail, name="course_detail"),
    path("kurs/<slug:slug>/test/", views.take_quiz, name="take_quiz"),
    path("natija/<int:attempt_id>/", views.quiz_result, name="quiz_result"),
]
