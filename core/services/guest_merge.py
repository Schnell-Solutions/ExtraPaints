"""Merge guest session saves into the authenticated user's account on login."""

from colors.models import SavedColor
from ideas.models import SavedIdea
from products.models import SavedProducts

from .guest_saves import SESSION_KEYS


def merge_guest_saves_into_user(request, user):
    """Copy session guest save IDs into DB rows; keep union of both."""
    if not user or not user.is_authenticated:
        return

    product_ids = request.session.get(SESSION_KEYS['product'], [])
    for pid in product_ids:
        try:
            SavedProducts.objects.get_or_create(user=user, product_id=int(pid))
        except (ValueError, TypeError):
            continue

    color_ids = request.session.get(SESSION_KEYS['color'], [])
    for cid in color_ids:
        try:
            SavedColor.objects.get_or_create(user=user, color_id=int(cid))
        except (ValueError, TypeError):
            continue

    idea_ids = request.session.get(SESSION_KEYS['idea'], [])
    for iid in idea_ids:
        try:
            SavedIdea.objects.get_or_create(user=user, idea_id=int(iid))
        except (ValueError, TypeError):
            continue

    for key in SESSION_KEYS.values():
        request.session.pop(key, None)
    request.session.modified = True
