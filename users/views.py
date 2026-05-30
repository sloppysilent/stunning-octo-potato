# users/views.py
from http import HTTPStatus

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (ChangePasswordForm, UserEditForm, UserLoginForm,
                    UserRegistrationForm)
from .models import Skill, User

SKILLS_API_LIMIT = 10


def paginate_queryset(queryset, request, per_page=12):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page")
    return paginator.get_page(page)


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:login")
    else:
        form = UserRegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
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
    logout(request)
    return redirect("projects:project_list")


def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, "users/user-details.html", {"user": user})


@login_required
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
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


def users_list(request):
    skill_name = request.GET.get("skill")
    users = User.objects.order_by("id")
    all_skills = Skill.objects.all().order_by("name")
    active_skill = None

    if skill_name:
        users = users.filter(skills__name=skill_name)
        active_skill = skill_name

    users_page = paginate_queryset(users, request)

    return render(
        request,
        "users/participants.html",
        {
            "participants": users_page,
            "all_skills": all_skills,
            "active_skill": active_skill,
            "is_paginated": users_page.has_other_pages(),
        },
    )


@login_required
def add_skill(request, user_id):
    user = get_object_or_404(User, id=user_id)
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
            skill = Skill.objects.get(id=skill_id)
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
    user = get_object_or_404(User, id=user_id)
    skill = get_object_or_404(Skill, id=skill_id)
    if request.user != user:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    if request.method == "POST":
        if user.skills.filter(id=skill.id).exists():
            user.skills.remove(skill)
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "error", "message": "Skill not found"})

    return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)


def skills_api(request):
    q = request.GET.get("q", "").strip()
    if q:
        skills = Skill.objects.filter(name__icontains=q).order_by("name")[
            :SKILLS_API_LIMIT
        ]
    else:
        skills = Skill.objects.all().order_by("name")[:SKILLS_API_LIMIT]

    return JsonResponse([{"id": s.id, "name": s.name} for s in skills], safe=False)
