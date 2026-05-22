from django.shortcuts import get_object_or_404

from colors.models import Color
from products.models import Product, Size


class QuoteItemValidationError(Exception):
    """Raised when quote line item data is invalid."""


def resolve_quote_line(*, product_id, color_id=None, size_id=None):
    """
    Resolve and validate product/color/size for a quote line.
    Only active products; color/size must belong to the product when configured.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)

    color = None
    if color_id:
        color = get_object_or_404(Color, id=color_id, is_active=True)
        if product.category.features_colors:
            if product.available_colors.exists() and not product.available_colors.filter(pk=color.pk).exists():
                raise QuoteItemValidationError('Selected color is not available for this product.')

    size = None
    if size_id:
        size = get_object_or_404(Size, id=size_id)
        if product.category.features_sizes:
            if product.available_sizes.exists() and not product.available_sizes.filter(pk=size.pk).exists():
                raise QuoteItemValidationError('Selected size is not available for this product.')

    return product, color, size
