from .quote import QuoteList

def quote_list_context(request):
    """
    Makes the quote list object available in all templates
    as a variable named 'quote_list'.
    """
    return {'quote_list': QuoteList(request)}