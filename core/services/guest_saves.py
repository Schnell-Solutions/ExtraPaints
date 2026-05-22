"""Session-based saves for visitors without an account."""

SESSION_KEYS = {
    'product': 'guest_saved_products',
    'color': 'guest_saved_colors',
    'idea': 'guest_saved_ideas',
}


def _ids(request, kind):
    return set(request.session.get(SESSION_KEYS[kind], []))


def is_saved(request, kind, item_id):
    """True if item is in the guest session save list."""
    return int(item_id) in _ids(request, kind)


def toggle(request, kind, item_id):
    item_id = int(item_id)
    key = SESSION_KEYS[kind]
    ids = _ids(request, kind)
    if item_id in ids:
        ids.remove(item_id)
        saved = False
    else:
        ids.add(item_id)
        saved = True
    request.session[key] = list(ids)
    request.session.modified = True
    return saved


def guest_saved_ids(request, kind):
    return list(_ids(request, kind))
