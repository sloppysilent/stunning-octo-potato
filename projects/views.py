# projects/views.py
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm
from .models import STATUS_CLOSED, STATUS_OPEN, Project


def paginate_queryset(queryset, request, per_page=12):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page")
    return paginator.get_page(page)


def project_list(request):
    projects = Project.objects.select_related("owner").order_by("-created_at")
    projects_page = paginate_queryset(projects, request)

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects_page,
            "is_paginated": projects_page.has_other_pages(),
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

    return render(request, "projects/create_project.html", {"form": form})


def project_detail(request, project_id):
    project = get_object_or_404(Project.objects.select_related("owner"), id=project_id)
    is_participant = request.user in project.participants.all()

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "is_participant": is_participant,
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
        "projects/edit_project.html",
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
