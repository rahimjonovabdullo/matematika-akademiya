from django.contrib.auth import views as auth_views
from django.urls import path

from . import manage_views, views

urlpatterns = [
    path("", views.home, name="home"),
    path("kirish/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("chiqish/", auth_views.LogoutView.as_view(), name="logout"),
    path("royxatdan-otish/", views.register, name="register"),
    path("kabinet/", views.dashboard, name="dashboard"),
    path("testlar/", views.tests_list, name="tests_list"),
    path("natijalarim/", views.results_list, name="results_list"),
    path("guruhlarim/", views.my_groups, name="my_groups"),
    path("liderlar/", views.leaderboard, name="leaderboard"),
    path("yordam/", views.help_page, name="help_page"),
    path("tolov/", views.payment_page, name="payment_page"),
    path(
        "sozlamalar/",
        auth_views.PasswordChangeView.as_view(
            template_name="academy/settings.html",
            success_url="/sozlamalar/?saved=1",
        ),
        name="settings_page",
    ),
    path("kurs/<slug:slug>/", views.course_detail, name="course_detail"),
    path("kurs/<slug:slug>/test/", views.take_quiz, name="take_quiz"),
    path("natija/<int:attempt_id>/", views.quiz_result, name="quiz_result"),

    # Boshqaruv paneli (faqat admin uchun)
    path("boshqaruv/", manage_views.manage_courses, name="manage_courses"),
    path("boshqaruv/sorovlar/", manage_views.manage_requests, name="manage_requests"),
    path("boshqaruv/kurs/yangi/", manage_views.manage_course_form, name="manage_course_new"),
    path("boshqaruv/kurs/<int:pk>/", manage_views.manage_course_form, name="manage_course_edit"),
    path("boshqaruv/kurs/<int:pk>/ochirish/", manage_views.manage_course_delete, name="manage_course_delete"),

    path("boshqaruv/kurs/<int:course_id>/darslar/", manage_views.manage_lessons, name="manage_lessons"),
    path("boshqaruv/kurs/<int:course_id>/darslar/yangi/", manage_views.manage_lesson_form, name="manage_lesson_new"),
    path("boshqaruv/kurs/<int:course_id>/darslar/<int:pk>/", manage_views.manage_lesson_form, name="manage_lesson_edit"),
    path("boshqaruv/kurs/<int:course_id>/darslar/<int:pk>/ochirish/", manage_views.manage_lesson_delete, name="manage_lesson_delete"),

    path("boshqaruv/kurs/<int:course_id>/testlar/", manage_views.manage_questions, name="manage_questions"),
    path("boshqaruv/kurs/<int:course_id>/testlar/yangi/", manage_views.manage_question_form, name="manage_question_new"),
    path("boshqaruv/kurs/<int:course_id>/testlar/<int:pk>/", manage_views.manage_question_form, name="manage_question_edit"),
    path("boshqaruv/kurs/<int:course_id>/testlar/<int:pk>/ochirish/", manage_views.manage_question_delete, name="manage_question_delete"),
]
