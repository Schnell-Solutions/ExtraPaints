from django.core.paginator import Paginator


CATALOG_PAGE_SIZE = 24


def paginate_queryset(queryset, request, *, per_page=CATALOG_PAGE_SIZE):
    """Paginate a queryset; reads ?page= from GET."""
    try:
        page_num = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page_num = 1
    paginator = Paginator(queryset, per_page)
    page = paginator.get_page(page_num)
    return page, paginator
