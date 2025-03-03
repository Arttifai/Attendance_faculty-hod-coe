from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers

class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        return response

class SessionValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        protected_paths = ['/loginstaff', '/loginhod', '/loginadmin']
        if request.path in protected_paths and not request.session.get('user_id'):
            return redirect('login')
        return self.get_response(request)
