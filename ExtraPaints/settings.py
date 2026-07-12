import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))


def _csv_hosts(name, default=""):
    return [h.strip() for h in os.getenv(name, default).split(",") if h.strip()]


def _env_flag(name, default="0"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes")


# DEBUG=1 in .env for local runserver (static/media URLs). DEBUG=0 for production.
DEBUG = _env_flag("DEBUG", "1" if os.getenv("DEBUG") is None else "0")

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret")
if not DEBUG and (not SECRET_KEY or SECRET_KEY == "unsafe-secret"):
    raise ImproperlyConfigured("Set a strong SECRET_KEY in the environment for production (DEBUG=0).")


ALLOWED_HOSTS = _csv_hosts("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

CSRF_TRUSTED_ORIGINS = _csv_hosts("CSRF_TRUSTED_ORIGINS")
if DEBUG and not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [
        'http://127.0.0.1:8000',
        'http://localhost:8000',
        'http://127.0.0.1:8001',
        'http://localhost:8001',
    ]

# Public site URL for sitemap/robots (e.g. https://www.extrapaints.co.ke). Falls back to request host in views.
PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "").rstrip("/")

# Use Tailwind CDN (dev only). Production: run `npm run build:css` and leave this unset/0.
USE_TAILWIND_CDN = _env_flag("TAILWIND_CDN", "1" if DEBUG else "0")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    'core',
    'home',
    'accounts.apps.AccountsConfig',
    'colors',
    'products',
    'quote_request',
    'ideas',
    'portfolio',
    'guides',
    'affiliates',
]

REFERRAL_COOKIE_MAX_AGE = int(os.getenv('REFERRAL_COOKIE_MAX_AGE', str(60 * 60 * 24 * 60)))

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.csp_nonce.CSPNonceMiddleware',
    'affiliates.middleware.ReferralCaptureMiddleware',
    'core.middleware.cache_headers.CacheHeadersMiddleware',
    'core.middleware.csp.ContentSecurityPolicyMiddleware',
]

ROOT_URLCONF = 'ExtraPaints.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'quote_request.context_processors.quote_list_context',
                'home.context_processors.media_url',
                'home.context_processors.canonical_url',
                'home.context_processors.site_settings',
                'home.context_processors.conversion_context',
                'home.context_processors.seo_context',
                'home.context_processors.csp_nonce',
                'home.context_processors.referral_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ExtraPaints.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

_db_default = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3')
DATABASES = {
    'default': dj_database_url.config(
        default=_db_default,
        conn_max_age=600 if _db_default.startswith('postgres') else 0,
    ),
}
if _db_default.startswith('postgres'):
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True

if not DEBUG and 'test' not in sys.argv and _db_default.startswith('sqlite'):
    raise ImproperlyConfigured(
        'SQLite is blocked when DEBUG=0 (production mode). For local runserver, set DEBUG=1 in .env. '
        'For production, set DATABASE_URL to a PostgreSQL connection string.'
    )

SITE_ID = 1


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_OTP_LENGTH = 6
AUTH_OTP_TTL_SECONDS = 900
AUTH_OTP_MAX_ATTEMPTS = 5


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.getenv('TIME_ZONE', 'Africa/Nairobi')

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "assets",
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# HTTPS / cookie security (production)
# ---------------------------------------------------------------------------
# Previously, the block below ran whenever DEBUG=0 (e.g. DEBUG=0 in .env).
# That turned on SECURE_SSL_REDIRECT by default ("1"), so SecurityMiddleware
# redirected every http://127.0.0.1:8000/ request to https:// — which breaks
# `manage.py runserver` because the dev server only supports HTTP.
#
# if not DEBUG:
#     SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "1") == "1"
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = "DENY"
#     if os.getenv("SECURE_HSTS_SECONDS"):
#         SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
#         SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "1") == "1"
#         SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "0") == "1"
#
# Production behind nginx: set USE_SECURE_PROXY=1 and secure cookies; let nginx handle
# HTTP→HTTPS (SECURE_SSL_REDIRECT=0) to avoid redirect loops and broken health checks.
# ---------------------------------------------------------------------------
_production_mode = not DEBUG and 'test' not in sys.argv

if _production_mode or _env_flag("USE_SECURE_PROXY"):
    if _env_flag("USE_SECURE_PROXY", "1" if _production_mode else "0"):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if _env_flag("SECURE_SSL_REDIRECT"):
    SECURE_SSL_REDIRECT = True

if _production_mode or _env_flag("SESSION_COOKIE_SECURE"):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    if os.getenv("SECURE_HSTS_SECONDS"):
        SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
        SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "1") == "1"
        SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "0") == "1"

# ----------------------------------------------------------------------
#                         EMAIL CONFIGURATION
# ----------------------------------------------------------------------

# 1. Backend Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# HOST/PORT/USER/PASSWORD are loaded using os.getenv()
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 25)) # Cast to integer
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')


# 2. Dynamic Security Configuration (Based on Port: 465 is SSL)

if EMAIL_PORT == 465:
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
elif EMAIL_PORT == 587:
    # Port 587 (TLS/STARTTLS) is more common for modern SMTP/cPanel
    EMAIL_USE_SSL = False
    EMAIL_USE_TLS = True
else:
    # Default safe fallbacks
    EMAIL_USE_SSL = False
    EMAIL_USE_TLS = False


# 3. Default Sender Addresses (Branded)
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or '')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

if not DEBUG and 'test' not in sys.argv and not DEFAULT_FROM_EMAIL:
    raise ImproperlyConfigured(
        'Set DEFAULT_FROM_EMAIL or EMAIL_HOST_USER when DEBUG=0.'
    )


# 4. Key Business Recipients (The "TO" address for inquiries)

# The address that receives contact form inquiries (used in views.py)
SALES_TEAM_EMAIL = os.getenv('SALES_TEAM_EMAIL', 'sales@extrapaints.co.ke')

# The default admin email for error notifications
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'jamesmatata@schnell.solutions')

# ----------------------------------------------------------------------
# SEO & local business (structured data, footer, contact)
# ----------------------------------------------------------------------
BUSINESS_PHONE_PRIMARY = os.getenv('BUSINESS_PHONE_PRIMARY', '+254725752908')
BUSINESS_PHONE_SECONDARY = os.getenv('BUSINESS_PHONE_SECONDARY', '')
BUSINESS_WHATSAPP = os.getenv('BUSINESS_WHATSAPP', '254725752908')
COMPANY_FOUNDED_YEAR = int(os.getenv('COMPANY_FOUNDED_YEAR', '2015'))
BUSINESS_EMAIL = os.getenv('BUSINESS_EMAIL', 'info@extrapaints.co.ke')
QUOTE_RESPONSE_SLA = os.getenv('QUOTE_RESPONSE_SLA', 'Response within 24 hours')

SEO_LOCAL_BUSINESS = {
    'name': os.getenv('BUSINESS_NAME', 'ExtraPaints'),
    'description': (
        'Paint shop and professional coating supplier in Nairobi, Kenya — interior, exterior, '
        'and commercial systems with tailored quotations for contractors and distributors.'
    ),
    'street_address': os.getenv('BUSINESS_STREET', 'Nairobi, Kenya'),
    'city': os.getenv('BUSINESS_CITY', 'Nairobi'),
    'region': os.getenv('BUSINESS_REGION', 'Nairobi County'),
    'postal_code': os.getenv('BUSINESS_POSTAL', ''),
    'country': os.getenv('BUSINESS_COUNTRY_CODE', 'KE'),
    'country_name': os.getenv('BUSINESS_COUNTRY', 'Kenya'),
    'latitude': float(os.getenv('BUSINESS_LAT', '-1.286389')),
    'longitude': float(os.getenv('BUSINESS_LNG', '36.817223')),
    'telephone': [
        t for t in [
            BUSINESS_PHONE_PRIMARY,
            BUSINESS_PHONE_SECONDARY,
        ] if t
    ],
    'email': BUSINESS_EMAIL,
    'google_maps_url': os.getenv('GOOGLE_MAPS_URL', ''),
    'area_served': _csv_hosts('BUSINESS_AREA_SERVED', 'Nairobi,Eldoret,Kenya'),
    'same_as': [
        u for u in [
            os.getenv('SOCIAL_FACEBOOK', 'https://web.facebook.com/extrapaints.ke'),
            os.getenv('SOCIAL_LINKEDIN', 'https://www.linkedin.com/in/extrapaints-ltd-b5a2283a3'),
            os.getenv('SOCIAL_INSTAGRAM', 'https://www.instagram.com/extrapaints400/'),
            os.getenv('SOCIAL_TIKTOK', 'https://www.tiktok.com/@extrapaints400'),
        ] if u
    ],
    'opening_hours': [
        {
            '@type': 'OpeningHoursSpecification',
            'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'opens': os.getenv('BUSINESS_WEEKDAY_OPEN', '08:00'),
            'closes': os.getenv('BUSINESS_WEEKDAY_CLOSE', '17:00'),
        },
        {
            '@type': 'OpeningHoursSpecification',
            'dayOfWeek': 'Saturday',
            'opens': os.getenv('BUSINESS_SATURDAY_OPEN', '09:00'),
            'closes': os.getenv('BUSINESS_SATURDAY_CLOSE', '13:00'),
        },
    ],
}

# ----------------------------------------------------------------------
# Caching (set CACHE_URL=redis://127.0.0.1:6379/1 in production when Redis is available)
# ----------------------------------------------------------------------
_cache_backend = os.getenv('CACHE_URL', '').strip()
if _cache_backend:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _cache_backend,
            'KEY_PREFIX': 'extrapaints',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'extrapaints-local',
        }
    }
    if _production_mode:
        raise ImproperlyConfigured(
            'Set CACHE_URL (e.g. redis://redis:6379/1) when DEBUG=0 — required for '
            'rate limiting across Gunicorn workers.'
        )

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# File logging only when not in Docker (containers should log to stdout).
if not DEBUG and not _env_flag('DOCKER_LOG_STDOUT_ONLY', '0') and not os.path.exists('/.dockerenv'):
    _log_dir = BASE_DIR / 'logs'
    _log_dir.mkdir(exist_ok=True)
    LOGGING['handlers']['file'] = {
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': str(_log_dir / 'extrapaints.log'),
        'maxBytes': 5 * 1024 * 1024,
        'backupCount': 5,
        'formatter': 'verbose',
    }
    LOGGING['root']['handlers'] = ['console', 'file']

# ----------------------------------------------------------------------
# Content Security Policy (nonce appended per-request in CSP middleware)
# ----------------------------------------------------------------------
_csp_scripts = ["'self'", 'https://unpkg.com']
_csp_styles = ["'self'", 'https://fonts.googleapis.com']
if USE_TAILWIND_CDN:
    _csp_scripts.extend(["'unsafe-inline'", 'https://cdn.tailwindcss.com'])
    _csp_styles.extend(["'unsafe-inline'", 'https://cdn.tailwindcss.com'])
# Production: scripts use nonce; color swatches need inline style="background-color:#hex"
_csp_style_attr = ["'unsafe-inline'"] if not USE_TAILWIND_CDN else []

CSP_DIRECTIVES = [
    "default-src 'self'",
    f"script-src {' '.join(_csp_scripts)}",
    f"style-src {' '.join(_csp_styles)}",
    *([f"style-src-attr {' '.join(_csp_style_attr)}"] if _csp_style_attr else []),
    "font-src 'self' https://fonts.gstatic.com data:",
    "img-src 'self' data: https: blob:",
    "connect-src 'self'",
    "frame-src https://www.google.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
]

STATIC_VERSION = os.getenv('STATIC_VERSION', '3')

# ----------------------------------------------------------------------



