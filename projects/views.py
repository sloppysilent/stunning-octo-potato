# projects/views.py
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm
from .models import STATUS_CLOSED, STATUS_OPEN, Favorite, Project

PROJECTS_PER_PAGE = 12


def paginate_queryset(queryset, request, per_page=12):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page")
    return paginator.get_page(page)


def project_list(request):
    skill_name = request.GET.get("skill")
    projects = Project.objects.select_related("owner").order_by("-created_at")
    active_skill = None

    # Фильтрация по навыкам (Вариант 3)
    if skill_name:
        projects = projects.filter(required_skills__name=skill_name)
        active_skill = skill_name

    projects_page = paginate_queryset(projects, request, per_page=PROJECTS_PER_PAGE)

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects_page,
            "is_paginated": projects_page.has_other_pages(),
            "active_skill": active_skill,
        },
    )


@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:project_detail", project_id=project.id)
    else:
        form = ProjectForm()

    return render(request, "projects/create-project.html", {"form": form})


def project_detail(request, project_id):
    project = get_object_or_404(Project.objects.select_related("owner"), id=project_id)
    is_participant = request.user in project.participants.all()
    is_favorited = False
    
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(
            user=request.user, project=project
        ).exists()

    return render(
        request,
        "projects/project-details.html",
        {
            "project": project,
            "is_participant": is_participant,
            "is_favorited": is_favorited,
        },
    )


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("projects:project_detail", project_id=project.id)
    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        "projects/create-project.html",
        {
            "form": form,
            "project": project,
        },
    )


@login_required
def complete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    if request.method == "POST" and project.status == STATUS_OPEN:
        project.status = STATUS_CLOSED
        project.save()
        return JsonResponse(
            {
                "status": "ok",
                "project_status": STATUS_CLOSED,
            }
        )

    return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)


@login_required
def toggle_participate(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        is_participant = project.participants.filter(id=request.user.id).exists()

        if is_participant:
            project.participants.remove(request.user)
            is_now_participant = False
        else:
            project.participants.add(request.user)
            is_now_participant = True

        return JsonResponse(
            {
                "status": "ok",
                "is_participant": is_now_participant,
            }
        )

    return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
