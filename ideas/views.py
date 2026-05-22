from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils.html import strip_tags
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.pagination import paginate_queryset
from core.seo.breadcrumbs import build_breadcrumbs
from core.seo.helpers import schema_json_ld_blocks
from core.seo.schema import breadcrumb_list_json
from core.services.guest_saves import guest_saved_ids, is_saved as guest_is_saved
from core.services.save_toggle import handle_save_toggle
from .models import Idea, IdeaCategory, Tag, SavedIdea


def idea_list(request):
    ideas = Idea.objects.filter(is_active=True).prefetch_related('tags', 'category')
    categories = IdeaCategory.objects.all().order_by("name")
    tags = Tag.objects.all().order_by("name")

    category_slug = request.GET.get("category")
    tag_slug = request.GET.get("tag")
    query = request.GET.get("q")
    sort = request.GET.get("sort", "newest")

    if category_slug:
        ideas = ideas.filter(category__slug=category_slug)

    if tag_slug:
        ideas = ideas.filter(tags__slug=tag_slug)

    if query:
        ideas = ideas.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    if sort == "featured":
        ideas = ideas.order_by("-is_featured", "-created_at")
    else:
        ideas = ideas.order_by("-created_at")

    ideas = ideas.distinct()

    if request.user.is_authenticated:
        saved_idea_ids = set(
            SavedIdea.objects.filter(user=request.user).values_list('idea_id', flat=True)
        )
    else:
        saved_idea_ids = set(guest_saved_ids(request, 'idea'))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        page_obj, _ = paginate_queryset(ideas, request)
        payload = []
        for idea in page_obj:
            desc = strip_tags(idea.description or '')
            img = idea.get_display_image
            try:
                from core.images import thumbnail_for_image_url
                img = thumbnail_for_image_url(img, width=400) if img else img
            except Exception:
                pass
            payload.append({
                'id': idea.id,
                'title': idea.title,
                'url': idea.get_absolute_url(),
                'description_excerpt': (desc[:120] + '...') if len(desc) > 120 else desc,
                'image_url': img,
                'is_saved': idea.id in saved_idea_ids,
                'tags': [t.name for t in idea.tags.all()],
            })
        return JsonResponse({
            'ideas': payload,
            'page': page_obj.number,
            'num_pages': page_obj.paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        })

    page_obj, paginator = paginate_queryset(ideas, request)
    idea_list_items = []
    for idea in page_obj:
        idea.is_saved = idea.id in saved_idea_ids
        idea_list_items.append(idea)

    breadcrumbs = build_breadcrumbs(request, ('Inspiration', None))
    qs_parts = []
    if category_slug:
        qs_parts.append(f'category={category_slug}')
    if tag_slug:
        qs_parts.append(f'tag={tag_slug}')
    if query:
        qs_parts.append(f'q={query}')
    if sort and sort != 'newest':
        qs_parts.append(f'sort={sort}')

    return render(request, "ideas/idea_list.html", {
        "ideas": idea_list_items,
        "page_obj": page_obj,
        "paginator": paginator,
        "query_string": '&'.join(qs_parts),
        "categories": categories,
        "tags": tags,
        "selected_category": category_slug,
        "selected_tag": tag_slug,
        "search_query": query or "",
        "sort": sort,
        "breadcrumbs": breadcrumbs,
        "schema_json_ld_blocks": schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
        ),
    })


def idea_detail(request, slug):
    idea = get_object_or_404(
        Idea.objects.prefetch_related('images', 'tags', 'paint_colors'),
        slug=slug,
        is_active=True,
    )

    if request.user.is_authenticated:
        is_saved = SavedIdea.objects.filter(user=request.user, idea=idea).exists()
    else:
        is_saved = guest_is_saved(request, 'idea', idea.id)

    related_ideas = Idea.objects.filter(
        category=idea.category,
        is_active=True,
    ).exclude(id=idea.id).order_by('-created_at')[:4]

    breadcrumbs = build_breadcrumbs(
        request,
        ('Inspiration', 'idea_list'),
        (idea.title, None),
    )
    return render(request, "ideas/idea_detail.html", {
        "idea": idea,
        "is_saved": is_saved,
        "related_ideas": related_ideas,
        "breadcrumbs": breadcrumbs,
        "schema_json_ld_blocks": schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
        ),
        "link_colors": list(idea.paint_colors.filter(is_active=True)[:8]),
    })


@require_POST
def save_idea_toggle(request):
    idea_id = request.POST.get('idea_id')
    if not idea_id:
        return JsonResponse({'status': 'error', 'message': 'Idea ID is required.'}, status=400)

    try:
        idea = Idea.objects.get(id=idea_id, is_active=True)
    except Idea.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Idea not found.'}, status=404)

    return handle_save_toggle(
        request,
        kind='idea',
        item=idea,
        saved_model=SavedIdea,
        relation_field='idea',
    )
