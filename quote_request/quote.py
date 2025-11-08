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

    def add(self, product, color, size, quantity):
        """
        Adds a 'virtual' product variant to the quote list.
        We create a unique key for the (product, color, size) combo.
        """
        # Create a unique key for this specific combination
        item_key = f"{product.id}_{color.id}_{size.id}"

        # Add or update the item
        self.quote_list[item_key] = {
            'product_id': product.id,
            'color_id': color.id,
            'size_id': size.id,
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
        """
        This is the new "magic" part.
        It loops over the session data and fetches the *actual*
        objects from the database to display them.
        """
        # We need to import these models here
        from products.models import Product, Size
        from colors.models import Color

        item_keys = self.quote_list.keys()

        # Go through a copy of the list
        for item_key in list(item_keys):
            item_data = self.quote_list.get(item_key)
            if not item_data:
                continue  # Skip if item is malformed

            try:
                # Re-create the item for the template
                item = {
                    'key': item_key,
                    'product': Product.objects.get(id=item_data['product_id']),
                    'color': Color.objects.get(id=item_data['color_id']),
                    'size': Size.objects.get(id=item_data['size_id']),
                    'quantity': item_data['quantity']
                }
                yield item
            except (Product.DoesNotExist, Color.DoesNotExist, Size.DoesNotExist):
                # Self-healing: if a product, color, or size was deleted
                # remove this item from the list.
                self.remove(item_key)

    def __len__(self):
        """Returns the total number of items in the list."""
        return len(self.quote_list)

    def clear(self):
        del self.session['quote_list']
        self.save()