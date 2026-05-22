from django.http import JsonResponse

from core.services.guest_saves import toggle as guest_toggle
from core.services.saved_items import toggle_saved_item


def handle_save_toggle(
    request,
    *,
    kind: str,
    item,
    saved_model,
    relation_field: str,
):
    if request.user.is_authenticated:
        is_saved = toggle_saved_item(
            user=request.user,
            saved_model=saved_model,
            relation_field=relation_field,
            item=item,
        )
    else:
        is_saved = guest_toggle(request, kind, item.pk)
    return JsonResponse({'status': 'success', 'is_saved': is_saved})
