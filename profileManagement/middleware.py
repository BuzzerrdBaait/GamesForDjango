from django.utils import translation


class UserLanguageMiddleware:
    """
    Activates the language stored in the authenticated user's UserOptions
    for the duration of each request.  Falls back to English for guests.
    Must be placed after AuthenticationMiddleware in settings.MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = 'en'
        if request.user.is_authenticated:
            try:
                language = request.user.options.language
            except Exception:
                pass

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

        response = self.get_response(request)

        translation.deactivate()
        return response
