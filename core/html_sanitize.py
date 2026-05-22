"""Sanitize rich HTML from trusted staff (guides, newsletters)."""

import bleach

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h2', 'h3', 'h4', 'ul', 'ol', 'li',
    'a', 'blockquote', 'img', 'span', 'div',
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'loading'],
    '*': ['class'],
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(html: str) -> str:
    if not html:
        return ''
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
