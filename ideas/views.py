from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Idea, Category, Tag, SavedIdea
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


def idea_list(request):
    """
    Displays all active ideas with dynamic filtering by category and tag.
    """
    ideas = Idea.objects.filter(is_active=True).prefetch_related('tags', 'category')
    categories = Category.objects.all().order_by("name")
    tags = Tag.objects.all().order_by("name")

    # --- Filters ---
    category_slug = request.GET.get("category")
    tag_slug = request.GET.get("tag")

    if category_slug:
        ideas = ideas.filter(category__slug=category_slug)

    if tag_slug:
        ideas = ideas.filter(tags__slug=tag_slug)

    # --- Search ---
    query = request.GET.get("q")
    if query:
        ideas = ideas.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    # --- Sort ---
    sort = request.GET.get("sort", "newest")
    if sort == "featured":
        ideas = ideas.order_by("-is_featured", "-created_at")
    else:
        ideas = ideas.order_by("-created_at")

    # Check for saved status for each idea
    if request.user.is_authenticated:
        saved_idea_ids = SavedIdea.objects.filter(user=request.user).values_list('idea_id', flat=True)
    else:
        saved_idea_ids = []

    # Attach save status to each idea object
    idea_list = []
    for idea in ideas.distinct():
        idea.is_saved = idea.id in saved_idea_ids
        idea_list.append(idea)

    return render(request, "ideas/idea_list.html", {
        "ideas": idea_list,
        "categories": categories,
        "tags": tags,
        "selected_category": category_slug,
        "selected_tag": tag_slug,
        "search_query": query or "",
        "sort": sort,
    })


def idea_detail(request, slug):
    """
    Show detailed information for a single idea, including its
    gallery, tags, and related shoppable paint colors.
    """
    idea = get_object_or_404(
        Idea.objects.prefetch_related(
            'images',
            'tags',
            'paint_colors'  # This is the "Improvement 2" field
        ),
        slug=slug,
        is_active=True
    )

    # Check if the current user has saved this idea
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedIdea.objects.filter(user=request.user, idea=idea).exists()

    # Get other ideas from the same category
    related_ideas = Idea.objects.filter(
        category=idea.category,
        is_active=True
    ).exclude(id=idea.id).order_by('?')[:4]  # '?' is random, use '-created_at' for newest

    return render(request, "ideas/idea_detail.html", {
        "idea": idea,
        "is_saved": is_saved,
        "related_ideas": related_ideas,
    })


@login_required
@require_POST
def save_idea_toggle(request):
    """
    AJAX view to save or unsave an idea for a user.
    """
    idea_id = request.POST.get('idea_id')
    if not idea_id:
        return JsonResponse({'status': 'error', 'message': 'Idea ID is required.'}, status=400)

    try:
        idea = Idea.objects.get(id=idea_id)
    except Idea.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Idea not found.'}, status=404)

    # Check if it already exists
    saved_obj, created = SavedIdea.objects.get_or_create(user=request.user, idea=idea)

    if created:
        # We just saved it
        is_saved = True
    else:
        # It existed, so we delete it (unsave)
        saved_obj.delete()
        is_saved = False

    return JsonResponse({'status': 'success', 'is_saved': is_saved})
