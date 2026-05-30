# users/views.py
from http import HTTPStatus

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from projects.models import Favorite, Project
from projects.team_finder import paginate_queryset

from .forms import (ChangePasswordForm, UserEditForm, UserLoginForm,
                    UserRegistrationForm)
from .models import Skill, User

SKILLS_API_LIMIT = 12
USERS_PER_PAGE = 12
PROJECTS_PER_PAGE = 12

FILTER_OWNERS_OF_FAVORITE_PROJECTS = "owners-of-favorite-projects"
FILTER_PARTICIPANTS_OF_MY_PROJECTS = "participants-of-my-projects"
FILTER_LIKERS_OF_MY_PROJECTS = "likers-of-my-projects"
FILTER_MEMBERS_OF_MY_PROJECTS = "members-of-my-projects"


def register(request):
    """Регистрация нового пользователя."""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:login")
    else:
        form = UserRegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    """Вход в систему."""
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                return redirect("projects:project_list")
            else:
                form.add_error(None, "Неверный email или пароль")
    else:
        form = UserLoginForm()
    return render(request, "users/login.html", {"form": form})


@login_required
def logout_view(request):
    """Выход из системы."""
    logout(request)
    return redirect("projects:project_list")


def user_detail(request, user_id):
    """Страница профиля пользователя."""
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return JsonResponse(
            {"status": "error", "message": "Пользователь не найден"}, status=HTTPStatus.NOT_FOUND
        )
    return render(request, "users/user-details.html", {"user": user})


@login_required
def edit_profile(request, user_id):
    """Редактирование профиля."""
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return JsonResponse(
            {"status": "error", "message": "Пользователь не найден"}, status=HTTPStatus.NOT_FOUND
        )
    if request.user != user:
        return redirect("users:user_detail", user_id=user.id)

    if request.method == "POST":
        form = UserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect("users:user_detail", user_id=user.id)
    else:
        form = UserEditForm(instance=user)

    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request, user_id):
    """Смена пароля."""
    if request.user.id != user_id:
        return redirect("projects:project_list")

    if request.method == "POST":
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:user_detail", user_id=request.user.id)
    else:
        form = ChangePasswordForm(user=request.user)

    return render(request, "users/change_password.html", {"form": form})


@login_required
def users_list(request):
    """Список всех пользователей с фильтрацией."""
    filter_type = request.GET.get("filter")
    skill_name = request.GET.get("skill")
    
    users = User.objects.order_by("-id")
    all_skills = Skill.objects.all().order_by("name")
    active_skill = None
    active_filter = None

    # Фильтрация по навыкам (Вариант 2)
    if skill_name:
        users = users.filter(skills__name=skill_name)
        active_skill = skill_name
    
    # Фильтрация по типам (Вариант 1)
    if filter_type and request.user.is_authenticated:
        if filter_type == FILTER_OWNERS_OF_FAVORITE_PROJECTS:
            # Авторы избранных проектов текущего пользователя
            favorite_project_ids = Favorite.objects.filter(
                user=request.user
            ).values("project_id")
            users = users.filter(owned_projects__id__in=favorite_project_ids).distinct()
            active_filter = filter_type
        elif filter_type == FILTER_PARTICIPANTS_OF_MY_PROJECTS:
            # Участники проектов текущего пользователя
            my_project_ids = Project.objects.filter(
                owner=request.user
            ).values("id")
            users = users.filter(participated_projects__id__in=my_project_ids).distinct()
            active_filter = filter_type
        elif filter_type == FILTER_LIKERS_OF_MY_PROJECTS:
            # Пользователи, которым нравятся мои проекты
            my_project_ids = Project.objects.filter(
                owner=request.user
            ).values("id")
            users = users.filter(
                favorite_projects__project_id__in=my_project_ids
            ).distinct()
            active_filter = filter_type
        elif filter_type == FILTER_MEMBERS_OF_MY_PROJECTS:
            # Участники моих проектов (то же что participants-of-my-projects)
            my_project_ids = Project.objects.filter(
                owner=request.user
            ).values("id")
            users = users.filter(participated_projects__id__in=my_project_ids).distinct()
            active_filter = filter_type

    users_page = paginate_queryset(users, request, per_page=USERS_PER_PAGE)

    return render(
        request,
        "users/participants.html",
        {
            "participants": users_page,
            "all_skills": all_skills,
            "active_skill": active_skill,
            "active_filter": active_filter,
            "is_paginated": users_page.has_other_pages(),
        },
    )


@login_required
def favorites_view(request):
    """Страница избранных проектов пользователя."""
    favorites = Favorite.objects.filter(user=request.user).select_related(
        "project__owner"
    ).order_by("-created_at")
    
    projects = [fav.project for fav in favorites]
    projects_page = paginate_queryset(projects, request, per_page=PROJECTS_PER_PAGE)
    
    return render(
        request,
        "projects/favorite_projects.html",
        {
            "projects": projects_page,
            "is_paginated": projects_page.has_other_pages(),
        },
    )


@login_required
def toggle_favorite(request, project_id):
    """Добавление/удаление проекта из избранного."""
    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Проект не найден"}, status=HTTPStatus.NOT_FOUND
        )
    
    if request.method == "POST":
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, project=project
        )
        
        if not created:
            # Если уже в избранном, удаляем
            favorite.delete()
            is_favorited = False
        else:
            is_favorited = True
        
        return JsonResponse({
            "status": "ok",
            "is_favorited": is_favorited,
        })
    
    return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)


@login_required
def add_skill(request, user_id):
    """Добавление навыка пользователю."""
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return JsonResponse(
            {"status": "error", "message": "Пользователь не найден"}, status=HTTPStatus.NOT_FOUND
        )
    if request.user != user:
        return JsonResponse(
            {"status": "error", "message": "Нет прав"},
            status=HTTPStatus.FORBIDDEN,
        )

    if request.method == "POST":
        skill_name = request.POST.get("name", "").strip()
        if not skill_name:
            return JsonResponse(
                {"status": "error", "message": "Название навыка не может быть пустым"},
                status=HTTPStatus.BAD_REQUEST,
            )

        skill_id = request.POST.get("skill_id")
        skill = None
        created = False

        if skill_id:
            skill = Skill.objects.filter(id=skill_id).first()
        else:
            skill, created = Skill.objects.get_or_create(name=skill_name)

        if skill and not user.skills.filter(id=skill.id).exists():
            user.skills.add(skill)
            return JsonResponse(
                {
                    "skill_id": skill.id,
                    "name": skill.name,
                    "created": created,
                    "added": True,
                }
            )

        return JsonResponse(
            {
                "skill_id": skill.id if skill else None,
                "name": skill.name if skill else "",
                "created": created,
                "added": False,
                "message": "Навык уже добавлен",
            }
        )


@login_required
def remove_skill(request, user_id, skill_id):
    """Удаление навыка у пользователя."""
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return JsonResponse(
            {"status": "error", "message": "Пользователь не найден"}, status=HTTPStatus.NOT_FOUND
        )
    skill = Skill.objects.filter(id=skill_id).first()
    if skill is None:
        return JsonResponse(
            {"status": "error", "message": "Навык не найден"}, status=HTTPStatus.NOT_FOUND
        )
    if request.user != user:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    if request.method == "POST":
        if user.skills.filter(id=skill.id).exists():
            user.skills.remove(skill)
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "error", "message": "Skill not found"})

    return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)


def skills_api(request):
    """API для получения списка навыков."""
    query = request.GET.get("q", "").strip()
    if query:
        skills = Skill.objects.filter(name__icontains=query).order_by("name")[
            :SKILLS_API_LIMIT
        ]
    else:
        skills = Skill.objects.all().order_by("name")[:SKILLS_API_LIMIT]

    return JsonResponse([{"id": skill.id, "name": skill.name} for skill in skills], safe=False)
