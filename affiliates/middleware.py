from affiliates.services import capture_referral_from_query, set_referral_cookie


class ReferralCaptureMiddleware:
    """
    Lightweight: on safe GET requests, capture ?ref= after server validation.
    Does not run on POST/AJAX-heavy paths beyond normal GET navigation.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'GET' and 'ref' in request.GET:
            affiliate = capture_referral_from_query(request)
            response = self.get_response(request)
            if affiliate:
                set_referral_cookie(response, affiliate)
            return response

        response = self.get_response(request)
        return response
