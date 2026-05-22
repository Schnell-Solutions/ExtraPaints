from django.db import models


def toggle_saved_item(*, user, saved_model: type[models.Model], relation_field: str, item) -> bool:
    """
    Toggle a user's saved-item row. Returns True if saved after toggle, False if removed.
    """
    lookup = {relation_field: item}
    saved_obj, created = saved_model.objects.get_or_create(user=user, **lookup)
    if created:
        return True
    saved_obj.delete()
    return False
