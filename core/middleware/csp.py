from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """CSP with per-request nonce for JSON-LD when using compiled CSS (no Tailwind CDN)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        base = getattr(settings, 'CSP_DIRECTIVES', [])
        if not base:
            return response

        use_cdn = getattr(settings, 'USE_TAILWIND_CDN', False)
        nonce = getattr(request, 'csp_nonce', '')
        directives = []

        for directive in base:
            if directive.startswith('script-src ') and not use_cdn and nonce:
                parts = ["'self'", 'https://unpkg.com', f"'nonce-{nonce}'"]
                directives.append(f"script-src {' '.join(parts)}")
            else:
                directives.append(directive)

        header = (
            'Content-Security-Policy-Report-Only'
            if settings.DEBUG
            else 'Content-Security-Policy'
        )
        response[header] = '; '.join(directives)
        return response
