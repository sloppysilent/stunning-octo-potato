from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("list/", views.users_list, name="users_list"),
    path("<int:user_id>/", views.user_detail, name="user_detail"),
    path("<int:user_id>/edit/", views.edit_profile, name="edit_profile"),
    path(
        "<int:user_id>/change_password/", views.change_password, name="change_password"
    ),
    path("skills/", views.skills_api, name="skills_api"),
    path("<int:user_id>/skills/add/", views.add_skill, name="add_skill"),
    path(
        "<int:user_id>/skills/<int:skill_id>/remove/",
        views.remove_skill,
        name="remove_skill",
    ),
]
