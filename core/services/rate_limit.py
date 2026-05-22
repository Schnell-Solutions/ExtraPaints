from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def rate_limit(key_prefix, *, limit=8, period=300, methods=('POST',)):
    """IP-based rate limit using cache incr (atomic when backend supports it)."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.method not in methods:
                return view_func(request, *args, **kwargs)

            cache_key = f'ratelimit:{key_prefix}:{client_ip(request)}'
            try:
                hits = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, period)
                hits = 1
            else:
                try:
                    cache.touch(cache_key, period)
                except Exception:
                    pass

            if hits > limit:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse(
                        {
                            'status': 'error',
                            'message': 'Too many submissions. Please wait a few minutes.',
                        },
                        status=429,
                    )
                from django.contrib import messages
                from django.shortcuts import redirect

                messages.error(
                    request, 'Too many submissions. Please try again in a few minutes.'
                )
                return redirect(request.META.get('HTTP_REFERER', '/'))

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
