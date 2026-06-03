"""Default SEO copy and indexing rules."""

DEFAULT_SITE_TITLE = 'ExtraPaints | Professional Paint Supply & Quotes — Nairobi, Kenya'
DEFAULT_META_DESCRIPTION = (
    'ExtraPaints — professional paint supply in Nairobi and Kenya. Browse interior and exterior '
    'products, explore our color library, read guides, and request tailored quotations for your project.'
)
DEFAULT_OG_DESCRIPTION = (
    'B2B paint supply, color systems, and custom quotations for commercial and residential '
    'projects across Kenya.'
)

NOINDEX_URL_NAMES = frozenset({
    'login',
    'register',
    'logout',
    'profile',
    'update_profile',
    'change_password',
    'request_account_deletion',
    'account_deletion_submitted',
    'password_reset_request',
    'password_reset_done',
    'password_reset_confirm',
    'password_reset_verify',
    'password_reset_set',
    'verify_email',
    'verify_email_otp',
    'resend_verification',
    'verification_pending',
    'quote_detail',
    'quote_add',
    'quote_remove',
    'quote_update',
    'quote_submitted',
    'my_collection',
    'quick_inquiry',
    'subscribe_newsletter',
    'live_search',
    'random_hero_color',
})
