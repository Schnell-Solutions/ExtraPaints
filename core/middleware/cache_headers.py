from django.conf import settings


class CacheHeadersMiddleware:
    """Add cache headers for static assets and short cache for safe GET APIs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path

        if path.startswith(settings.STATIC_URL) or path.startswith('/static/'):
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
            return response

        if path.startswith(settings.MEDIA_URL) or path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=86400'
            return response

        if path.startswith('/ajax/home-products'):
            response['Cache-Control'] = 'public, max-age=300'
            return response

        return response
