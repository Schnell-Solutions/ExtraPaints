import secrets


class CSPNonceMiddleware:
    """Attach a per-request nonce for CSP script-src (JSON-LD and future inline needs)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        return self.get_response(request)
