# projects/team_finder.py
"""Модуль для поиска команды и утилит."""

from django.core.paginator import Paginator


def paginate_queryset(queryset, request, per_page=12):
    """Пагинация queryset."""
    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page")
    return paginator.get_page(page)
