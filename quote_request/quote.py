class QuoteList:
    """A simple session-based list for quote requests."""

    def __init__(self, request):
        self.session = request.session
        quote_list = self.session.get('quote_list')
        if not quote_list:
            quote_list = self.session['quote_list'] = {}
        self.quote_list = quote_list

    def save(self):
        self.session.modified = True

    def add(self, product, quantity, color=None, size=None):
        """
        Adds a product to the quote list. Color and size are optional.
        """
        product_id = str(product.id)
        color_id = str(color.id) if color else 'None'
        size_id = str(size.id) if size else 'None'

        # Create a unique key: product_ID_color_ID_size_ID
        item_key = f"{product_id}_{color_id}_{size_id}"

        # Add or update the item
        self.quote_list[item_key] = {
            'product_id': product.id,
            'color_id': color.id if color else None,
            'size_id': size.id if size else None,
            'quantity': quantity,
        }
        self.save()

    def update(self, item_key, quantity):
        """
        Updates the quantity for a specific item.
        If quantity is 0 or less, removes the item.
        """
        item_key = str(item_key)

        if item_key not in self.quote_list:
            # Nothing to update
            return

        if quantity > 0:
            # Update the quantity
            self.quote_list[item_key]['quantity'] = quantity
            self.save()
        else:
            # Quantity is 0 or less, so remove it
            self.remove(item_key)

    def remove(self, item_key):
        """Removes an item from the list using its unique key."""
        if item_key in self.quote_list:
            del self.quote_list[item_key]
            self.save()

    def __iter__(self):
        from products.models import Product, Size
        from colors.models import Color

        item_keys = list(self.quote_list.keys())
        for item_key in item_keys:
            item_data = self.quote_list.get(item_key)
            if not item_data:
                continue

            try:
                product = Product.objects.get(id=item_data['product_id'])

                # Handle optional color
                color = None
                if item_data['color_id'] is not None:
                    color = Color.objects.get(id=item_data['color_id'])

                # Handle optional size
                size = None
                if item_data['size_id'] is not None:
                    size = Size.objects.get(id=item_data['size_id'])

                item = {
                    'key': item_key,
                    'product': product,
                    'color': color,
                    'size': size,
                    'quantity': item_data['quantity']
                }
                yield item
            except (Product.DoesNotExist, Color.DoesNotExist, Size.DoesNotExist):
                self.remove(item_key)

    def __len__(self):
        """Returns the total number of items in the list."""
        return len(self.quote_list)

    def clear(self):
        del self.session['quote_list']
        self.save()